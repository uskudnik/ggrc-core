# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""This module contains special query helper class for query API."""

from ggrc import db
from ggrc import models

from ggrc.builder import json
from ggrc.converters.query_helper import QueryHelper
from ggrc.utils import benchmark


# pylint: disable=too-few-public-methods


def find_operation(expression):
  """Find name of operation in object query.

  Args:
    expression: An expression dictionary
  Returns:
    operation dictionary
  """
  if "object_name" in expression:
    return expression

  if "left" in expression:
    result = find_operation(expression["left"])
    if result:
      return result

  if "right" in expression:
    result = find_operation(expression["right"])
    if result:
      return result


class QueryAPIQueryHelper(QueryHelper):
  """Helper class for handling request queries for query API.

  query object = [
    {
      # the same parameters as in QueryHelper
      type: "values", "ids" or "count" - the type of results requested
      fields: [ a list of fields to include in JSON if type is "values" ]
    }
  ]

  After the query is done (by `get_results` method), the results are appended
  to each query object:

  query object with results = [
    {
      # the same fields as in QueryHelper
      values: [ filtered objects in JSON ] (present if type is "values")
      ids: [ ids of filtered objects ] (present if type is "ids")
      count: the number of objects filtered, after "limit" is applied
      total: the number of objects filtered, before "limit" is applied
  """
  def get_results(self):
    """Filter the objects and get their information.

    Updates self.query items with their results. The type of results required
    is read from "type" parameter of every object_query in self.query.

    Returns:
      list of dicts: same query as the input with requested results that match
                     the filter.
    """
    for object_query in self.query:
      object_type = object_query["object_name"]
      exp = object_query["filters"]["expression"]
      operation = find_operation(exp)
      is_snapshot = operation["op"]["name"] == "relevant_snapshot"

      query_type = object_query.get("type", "values")
      if query_type not in {"values", "ids", "count"}:
        raise NotImplementedError("Only 'values', 'ids' and 'count' queries "
                                  "are supported now")
      model = self.object_map[object_query["object_name"]]
      with benchmark("Get result set: get_results > _get_objects"):
        if is_snapshot:
          objects = self._get_snapshot_objects(object_query, operation,
                                               object_type)
        else:
          objects = self._get_objects(object_query)

      object_query["count"] = len(objects)
      with benchmark("get_results > _get_last_modified"):
        if is_snapshot:
          object_query["last_modified"] = max(
              {uat for _, _, _, _, _, _, uat in objects})
        else:
          object_query["last_modified"] = (
              self._get_last_modified(model, objects))
      with benchmark("serialization: get_results > _transform_to_json"):
        if query_type == "values":
          if is_snapshot:
            object_query["values"] = self._transform_snapshot_to_json(objects)
          else:
            object_query["values"] = self._transform_to_json(
                objects,
                object_query.get("fields"),
            )
      if query_type == "ids":
        if is_snapshot:
          object_query["ids"] = [_id for _id, _, _ in objects]
        else:
          object_query["ids"] = [o.id for o in objects]
    return self.query

  @staticmethod
  def _transform_snapshot_to_json(snapshots):
    """Transform returned snapshot iterable to JSON

    Args:
      snapshots: Iterable of tuples with (
          models.Snapshot.id,
          models.Snapshot.parent_type,
          models.Snapshot.parent_id,
          models.Snapshot.child_type,
          models.Snapshot.child_id,
          models.Snapshot.revision_id,
          models.Snapshot.updated_at)
    Return:
      List of dictionaries with keys id, parent_type, parent_id, child_type,
          child_id, revision_id, updated_at, type, selfLink, originalLink,
          viewLink.
    """
    revision_ids = {rid for _, _, _, _, _, rid, _ in snapshots}

    revision_content = db.session.query(
        models.Revision.id,
        models.Revision.content).filter(
            models.Revision.id.in_(revision_ids)
    )

    revisions = {rid: rcont for rid, rcont in revision_content}
    values = []
    for sid, ptype, pid, ctype, cid, rid, uat in snapshots:
      data = {
          "id": sid,
          "parent_type": ptype,
          "parent_id": pid,
          "child_type": ctype,
          "child_id": cid,
          "revision": revisions[rid],
          "updated_at": uat,
          "type": "Snapshot",
          "selfLink": "/api/snapshots/{}".format(sid),
          "originalLink": "/api/snapshots/{}".format(sid),
          "viewLink": "/snapshots/{}".format(sid)
      }
      values.append(data)
    return values

  @staticmethod
  def _transform_to_json(objects, fields=None):
    """Make a JSON representation of objects from the list."""
    objects_json = [json.publish(obj) for obj in objects]
    objects_json = json.publish_representation(objects_json)
    if fields:
      objects_json = [{f: o.get(f) for f in fields}
                      for o in objects_json]
    return objects_json

  @staticmethod
  def _get_last_modified(model, objects):
    """Get the time of last update of an object in the list."""
    if not objects or not hasattr(model, "updated_at"):
      return None
    else:
      return max(obj.updated_at for obj in objects)
