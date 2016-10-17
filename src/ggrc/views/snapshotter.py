# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Main view functions for snapshotter

This module handles all view related function for snapshotter. While the
operations itself are designed to be ran in the background and are not
accessible to users, this extends the operation output and amends it for
preview purposes.
"""

from collections import defaultdict
from logging import getLogger

from flask import request
from flask import json
from werkzeug.exceptions import BadRequest

from sqlalchemy.sql.expression import tuple_

from ggrc import db
from ggrc import models
from ggrc.models import all_models
from ggrc.snapshotter import create_snapshots
from ggrc.snapshotter import upsert_snapshots

from ggrc.login import login_required
from ggrc.utils import benchmark


# pylint: disable=invalid-name
logger = getLogger(__name__)


def get_object_history(_objects):
  """Return full object history for all objects

  Returns a full history for requested objects, grouped by type
  and ID. Result is dictionary of dictionary of list of 3-tuples.

  Args:
    _objects: An iterable of (type, id) pairs.
  Returns:
    A dictionary of dictionaries of list representing type-id hierarchy
    history["ObjectType"]["ID"] = [(revision ID,
                                    revision created at,
                                    revision content)]
  """

  with benchmark("Snapshotter.preview.get_object_history"):
    object_history = defaultdict(lambda: defaultdict(list))
    if _objects:
      all_revisions = db.session.query(
          models.Revision.resource_type,
          models.Revision.resource_id,
          models.Revision.id,
          models.Revision.created_at,
          models.Revision.content
      ).filter(
          tuple_(
              models.Revision.resource_type,
              models.Revision.resource_id
          ).in_(_objects)
      ).order_by(models.Revision.id.asc())
      for rtype, rid, _id, rcreated, rcontent in all_revisions:
        object_history[rtype][rid] += [(_id, rcreated, rcontent)]
    return object_history


def parse_operation(operation_response):
  """Parse response from snapshotter operations

  Args:
    operation_response: A OperationResponse named tuple returned by a
      snapshotter operation.
  Returns:
    grouped: A dict of dicts of list containing full object history.
    children: Objects on which a certain operation took place and what
      revisions were used for that snapshot.
  """
  with benchmark("Snapshotter.preview.parse_operation"):
    pairs = operation_response.response
    revisions = operation_response.data["revisions"]

    if operation_response.type == "update":
      revisions = operation_response.data["revisions"]["new"]

    children = {child for _, child in pairs}
    grouped = defaultdict(lambda: defaultdict(list))

    for pair in pairs:
      grouped[pair.parent.type][pair.parent.id] = [{
          "child": pair.child.to_json_stub(),
          "revision_id": revisions[pair],
      }]
    return grouped, children


def handle_create_preview(objs):
  """Handle upsert preview for parent objects

  Args:
    objs: Iterable of parent objects
  Returns:
    Dictionary containing created responses and full object
    history for all objects that were created. Updated key is included but
    left empty.
  """
  created = create_snapshots(objs, None, dry_run=True)
  created_response, created_children = parse_operation(
      created.response["create"])
  return {
      "created": created_response,
      "updated": {},
      "history": get_object_history(created_children)
  }


def handle_upsert_preview(objs):
  """Handle upsert preview for parent objects

  Args:
    objs: Iterable of parent objects
  Returns:
    Dictionary containing created and updated responses and full object
    history for all objects that was either created or updated.
  """
  with benchmark("Snapshotter.preview.handle_upsert_preview"):
    upserted = upsert_snapshots(objs, None, dry_run=True)
    with benchmark("Snapshotter.preview.handle_upsert_preview.parse create"):
      created_response, created_children = parse_operation(
          upserted.response["create"])
    with benchmark("Snapshotter.preview.handle_upsert_preview.parse update"):
      updated_response, updated_children = parse_operation(
          upserted.response["update"])

    modified = created_children | updated_children

    return {
        "created": created_response,
        "updated": updated_response,
        "history": get_object_history(modified)
    }


def init_snapshotter_views(app):
  """Initialize views for import and export."""

  # pylint: disable=unused-variable
  # The view function trigger a false unused-variable.
  @app.route("/_service/snapshotter/preview", methods=["GET"])
  @login_required
  def handle_preview():
    """Handle preview operations for create and update"""
    preview_handlers = {
        "create": handle_create_preview,
        "upsert": handle_upsert_preview
    }

    with benchmark("Snapshotter.handle preview"):
      request_dict = request.get_json()
      if "snapshotter" in request_dict:
        settings = request_dict["snapshotter"]
        operation = settings["operation"]
        # TODO secure this a bit better?
        parent_stub = settings["parent"]
        model = getattr(all_models, parent_stub["type"])
        parent = {model.query.get(parent_stub["id"])}
        if settings["operation"] in preview_handlers:
          g = preview_handlers[operation]
          response_json = json.dumps(g(parent))
        else:
          raise BadRequest("Unsupported operation")

      headers = [("Content-Type", "application/json")]
      return app.make_response((response_json, 200, headers))
