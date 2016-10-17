# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Various simple helper functions for snapshot generator"""

import collections
import json


from sqlalchemy.sql.expression import tuple_

from ggrc import db
from ggrc import models
from ggrc.models.background_task import create_task
from ggrc.snapshotter.datastructures import Stub
from ggrc.snapshotter.datastructures import Pair
from ggrc.utils import benchmark


def get_revisions(pairs, revisions, filters=None):
  """Retrieve revision ids for pairs

  Args:
    pairs: set([(parent_1, child_1), (parent_2, child_2), ...])
    revisions: dict({(parent, child): revision_id, ...})
    filters: predicate
  """
  with benchmark("snapshotter.helpers.get_revisions"):
    revision_id_cache = dict()

    if pairs:
      with benchmark("get_revisions.create caches"):
        child_stubs = {pair.child for pair in pairs}

        with benchmark("get_revisions.create child -> parents cache"):
          parents_cache = collections.defaultdict(set)
          for parent, child in pairs:
            parents_cache[child].add(parent)

      with benchmark("get_revisions.retrieve revisions"):
        query = db.session.query(
            models.Revision.id,
            models.Revision.resource_type,
            models.Revision.resource_id).filter(
            tuple_(
                models.Revision.resource_type,
                models.Revision.resource_id).in_(child_stubs)
        ).order_by(models.Revision.id.desc())
        if filters:
          for _filter in filters:
            query = query.filter(_filter)

      with benchmark("get_revisions.create revision_id cache"):
        for revid, restype, resid in query:
          child = Stub(restype, resid)
          for parent in parents_cache[child]:
            key = Pair(parent, child)
            if key in revisions:
              if revid == revisions[key]:
                revision_id_cache[key] = revid
            else:
              if key not in revision_id_cache:
                revision_id_cache[key] = revid
    return revision_id_cache


def get_relationships(relationships):
  """Retrieve relationships

  Args:
    relationships:
  """
  with benchmark("snapshotter.helpers.get_relationships"):
    if relationships:
      relationship_columns = db.session.query(
          models.Relationship.id,
          models.Relationship.modified_by_id,
          models.Relationship.created_at,
          models.Relationship.updated_at,
          models.Relationship.source_type,
          models.Relationship.source_id,
          models.Relationship.destination_type,
          models.Relationship.destination_id,
          models.Relationship.context_id,
      )

      return relationship_columns.filter(
          tuple_(
              models.Relationship.source_type,
              models.Relationship.source_id,
              models.Relationship.destination_type,
              models.Relationship.destination_id,
          ).in_(relationships)
      ).union(
          relationship_columns.filter(
              tuple_(
                  models.Relationship.destination_type,
                  models.Relationship.destination_id,
                  models.Relationship.source_type,
                  models.Relationship.source_id
              ).in_(relationships)
          )
      )
    else:
      return set()


def get_event(_object, action):
  """Retrieve the last event for parent objects that performed
  PUT/POST/IMPORT/Event.action action."""
  with benchmark("snapshotter.helpers.get_event"):
    event = db.session.query(
        models.Event.id,
        models.Event.resource_type,
        models.Event.resource_id).filter(
        models.Event.resource_type == _object.type,
        models.Event.resource_id == _object.id,
        models.Event.action == action).order_by(
        models.Event.id.desc()).first()
    if not event:
      raise Exception("No event found!")
    return event


def get_snapshots(objects=None, ids=None):
  with benchmark("snapshotter.helpers.get_snapshots"):
    if objects and ids:
      raise Exception(
          "Insert only iterable of (parent, child) tuples or set of IDS")
    columns = db.session.query(
        models.Snapshot.id,
        models.Snapshot.context_id,
        models.Snapshot.created_at,
        models.Snapshot.updated_at,
        models.Snapshot.parent_type,
        models.Snapshot.parent_id,
        models.Snapshot.child_type,
        models.Snapshot.child_id,
        models.Snapshot.revision_id,
        models.Snapshot.modified_by_id,
    )
    if objects:
      return columns.filter(
          tuple_(
              models.Snapshot.parent_type,
              models.Snapshot.parent_id,
              models.Snapshot.child_type,
              models.Snapshot.child_id
          ).in_({(parent.type, parent.id, child.type, child.id)
                 for parent, child in objects}))
    if ids:
      return columns.filter(
          models.Snapshot.id.in_(ids))
    return set()


def create_snapshot_dict(pair, revision_id, user_id, context_id):
  """Create dictionary representation of snapshot"""
  parent, child = pair.to_2tuple()
  return {
      "parent_type": parent.type,
      "parent_id": parent.id,
      "child_type": child.type,
      "child_id": child.id,
      "revision_id": revision_id,
      "modified_by_id": user_id,
      "context_id": context_id
  }


def create_snapshot_revision_dict(action, event_id, snapshot,
                                  user_id, context_id):
  """Create dictionary representation of snapshot revision"""
  return {
      "action": action,
      "event_id": event_id,
      "content": create_snapshot_log(snapshot),
      "modified_by_id": user_id,
      "resource_id": snapshot[0],
      "resource_type": "Snapshot",
      "context_id": context_id
  }


def create_relationship_dict(source, destination, user_id, context_id):
  """Create dictionary representation of relationship"""
  return {
      "source_type": source.type,
      "source_id": source.id,
      "destination_type": destination.type,
      "destination_id": destination.id,
      "modified_by_id": user_id,
      "context_id": context_id,
  }


def create_relationship_revision_dict(action, event, relationship,  # noqa # pylint: disable=invalid-name
                                      user_id, context_id):
  """Create dictionary representation of relationship revision"""
  return {
      "action": action,
      "event_id": event,
      "content": create_relationship_log(relationship),
      "modified_by_id": user_id,
      "resource_id": relationship[0],
      "resource_type": "Relationship",
      "context_id": context_id
  }


def create_snapshot_log(snapshot):
  """Create dictionary representation of snapshot log entry"""
  (sid, context_id, created_at, updated_at,
   parent_type, parent_id,
   child_type, child_id,
   revision_id, modified_by_id) = snapshot
  return {
      "id": sid,
      "context_id": context_id,
      "created_at": created_at,
      "updated_at": updated_at,
      "parent_type": parent_type,
      "parent_id": parent_id,
      "child_type": child_type,
      "child_id": child_id,
      "revision_id": revision_id,
      "modified_by_id": modified_by_id,
  }


def create_relationship_log(relationship):
  """Create dictionary representation of relationship log entry"""
  (rid,
   modified_by_id,
   created_at,
   updated_at,
   source_type,
   source_id,
   destination_type,
   destination_id,
   context_id,
   ) = relationship
  return {
      "id": rid,
      "context_id": context_id,
      "created_at": created_at,
      "updated_at": updated_at,
      "source_type": source_type,
      "source_id": source_id,
      "destination_type": destination_type,
      "destination_id": destination_id,
      "modified_by_id": modified_by_id,
  }


def create_dry_run_response(pairs, old_revisions, new_revisions):
  with benchmark("create_dry_run_response"):
    response = dict()
    for pair in pairs:
      if pair.parent not in response:
        response[pair.parent] = {}

      old_revision_id = old_revisions.get(pair)
      new_revision_id = new_revisions.get(pair)
      if old_revision_id != new_revision_id:
        response[pair.parent][pair.child] = (old_revision_id, new_revision_id)
    return response


def create_bg_task(method, chunk):
  """Create background task"""
  return create_task(
      name="{}-SNAPSHOTS-".format(method),
      url="/_process_snapshots",
      queued_callback=None, parameters=json.dumps(chunk))
