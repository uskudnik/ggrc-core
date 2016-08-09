# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import json

from sqlalchemy.sql.expression import tuple_
from sqlalchemy.sql.expression import bindparam

from ggrc import db
from ggrc import models
from ggrc.models.background_task import create_task
from ggrc.login import get_current_user_id
from ggrc.snapshoter.rules import Attr
from ggrc.services.common import Resource
from ggrc.snapshoter.rules import get_rules
from ggrc.utils import benchmark


QUEUE_SIZE = 1000


class SnapshotGenerator(object):
  """Geneate snapshots per rules of all connected objects"""

  def __init__(self, chunking=True):
    self._RULES = get_rules()
    self.OPERATION_HANDLERS = {
        "create": self._create,
        "update": self._update
    }

    self.parent_objects = set()
    self.children_objects = set()
    self.context_cache = dict()
    self.snapshotable_objects = dict()
    self.chunking = chunking

  def add_parent_object(self, obj):
    """Add parent object and automatically scan neighbourhood for snapshottable
    objects."""
    key = (obj.type, obj.id)
    if key not in self.parent_objects:
      objs = self._get_snapshotable_objects(obj)
      self.parent_objects.add(key)
      self.context_cache[key] = obj.context_id
      self.children_objects = self.children_objects | objs
      self.snapshotable_objects[key] = objs
    return self.parent_objects

  def add_pairs(self, parent, children):
    """Directly add parent object and children that should be snapshotted."""
    _type, _id = parent
    model = getattr(models, _type)
    parent_object = db.session.query(model).filter(model.id == _id).first()
    if parent_object:
      self.parent_objects.add(parent)
      self.snapshotable_objects[parent] = children
      self.children_objects = children
      self.context_cache[parent] = parent_object.context_id
    else:
      raise Exception("No such parent object exists!")

  def _get_events(self, action, objects):
    """Retrieve the last event for parent objects that performed
    PUT/POST/IMPORT/Event.action action."""
    events_query = db.session.query(
        models.Event.id,
        models.Event.resource_type,
        models.Event.resource_id).filter(
        tuple_(
            models.Event.resource_type,
            models.Event.resource_id,
            models.Event.action).in_(
                [(_type, _id, action)
                 for _type, _id in objects])).order_by(models.Event.id.desc())

    all_events = events_query.all()
    events = dict()
    for eid, ert, erid in all_events:
      key = (ert, erid)
      if key not in events:
        events[key] = eid
    return events

  def _create_bg_task(self, method, chunk):
    """Create background task"""
    return create_task(
        name="{}-SNAPSHOTS-".format(method),
        url="/_process_snapshots",
        queued_callback=None, parameters=json.dumps(chunk))

  def _get_snapshotable_objects(self, obj):
    """Get snapshottable objects from parent object's neighbourhood."""
    object_rules = self._RULES.rules[obj.type]

    related_mappings = obj.related_objects({
        rule for rule in object_rules["fst"] if isinstance(rule, basestring)})

    direct_mappings = {getattr(obj, rule.name)
                       for rule in object_rules["fst"]
                       if isinstance(rule, Attr)}

    related_objects = related_mappings | direct_mappings

    return {(sndobj.type, sndobj.id)
            for fstobj in related_objects
            for sndobj in fstobj.related_objects(object_rules["snd"])}

  def update(self, method):
    """Update parent object's snapshots and split in chunks if there are too
    many of them."""
    return self.create_chunks(self._update, method=method)

  def _update(self, method):
    """Update (or create) parent objects' snapshots and create revisions for
    them."""
    user_id = get_current_user_id()
    engine = db.engine
    missed_keys = set()
    revision_id_cache = dict()
    snapshot_cache = dict()
    existing_snapshot_keys = set()
    modified_snapshot_keys = set()
    unmodified_snapshot_keys = set()
    data_payload_create = list()
    data_payload_update = list()
    revision_payload = list()

    with benchmark("Batch UPDATE snapshots"):
      with benchmark("Retrieve existing snapshots"):
        existing_snapshots = db.session.query(
            models.Snapshot.id,
            models.Snapshot.parent_type,
            models.Snapshot.parent_id,
            models.Snapshot.child_type,
            models.Snapshot.child_id,
            models.Snapshot.revision_id,
        ).filter(tuple_(
            models.Snapshot.parent_type, models.Snapshot.parent_id
        ).in_(self.parent_objects)).all()

      for sid, ptype, pid, ctype, cid, revid in existing_snapshots:
        parent_key = (ptype, pid)
        child_key = (ctype, cid)
        snapshot_cache[child_key] = [sid, revid, parent_key]
        existing_snapshot_keys.add(child_key)

      deleted_snapshot_keys = existing_snapshot_keys - self.children_objects

      with benchmark("Retrieve latest revisions"):
        revisions = db.session.query(
            models.Revision.id, models.Revision.resource_type,
            models.Revision.resource_id).filter(
                models.Revision.action.in_(["created", "modified"])
        ).filter(
            tuple_(
                models.Revision.resource_type,
                models.Revision.resource_id).in_(self.children_objects)
        ).order_by(models.Revision.id.desc()).all()

      for revid, restype, resid in revisions:
        key = (restype, resid)
        if key not in revision_id_cache:
          revision_id_cache[key] = revid

      with benchmark("Build models.Snapshot payload"):
        for parent_key in self.parent_objects:
          for child_key in self.snapshotable_objects[parent_key]:
            if child_key in revision_id_cache:
              if child_key in existing_snapshot_keys:
                sid, revid, _ = snapshot_cache[child_key]
                latest_rev = revision_id_cache[child_key]
                if revid != latest_rev:
                  modified_snapshot_keys.add(sid)
                  data_payload_update += [{
                      "_id": sid,
                      "_revision_id": latest_rev,
                      "_modified_by_id": user_id
                  }]
                else:
                  unmodified_snapshot_keys.add(sid)
              else:
                data_payload_create += [{
                    "parent_type": parent_key[0],
                    "parent_id": parent_key[1],
                    "child_type": child_key[0],
                    "child_id": child_key[1],
                    "revision_id": revision_id_cache[child_key],
                    "modified_by_id": user_id,
                    "context_id": self.context_cache[parent_key]
                }]
            else:
              missed_keys.add(child_key)

      with benchmark("INSERT and UPDATE models.Snapshot"):
        engine.execute(models.Snapshot.__table__.insert(), data_payload_create)
        update_sql = models.Snapshot.__table__.update().where(
            models.Snapshot.id == bindparam("_id")).values(
            revision_id=bindparam("_revision_id"),
            modified_by_id=bindparam("_modified_by_id"))
        if data_payload_update:
          engine.execute(update_sql, data_payload_update)
        db.session.commit()

      # Create revisions for snapshots
      touched_snapshots = {(ptype, pid, ctype, cid)
                           for ptype, pid in self.snapshotable_objects
                           for ctype, cid in self.snapshotable_objects[
                           (ptype, pid)]}
      snapshots = db.session.query(models.Snapshot).filter(
          tuple_(
              models.Snapshot.parent_type, models.Snapshot.parent_id,
              models.Snapshot.child_type, models.Snapshot.child_id).in_(
                  touched_snapshots)).all()

      snapshot_ids = {sh.id for sh in snapshots}
      snapshots = {sh.id: sh for sh in snapshots}
      created_snapshots = (snapshot_ids -
                           existing_snapshot_keys -
                           modified_snapshot_keys -
                           unmodified_snapshot_keys -
                           deleted_snapshot_keys)

      events = self._get_events(method, self.parent_objects)

      for snapshot in snapshots.values():
        if snapshot.id in unmodified_snapshot_keys:
          continue
        parent = snapshot.parent
        parent_key = (parent.type, parent.id)
        event = events[parent_key]
        action = ""
        if snapshot.id in created_snapshots:
          action = "created"
        elif snapshot.id in modified_snapshot_keys:
          action = "modified"
        revision_payload += [{
            "action": action,
            "event_id": event,
            "content": snapshot.log_json(),
            "modified_by_id": user_id,
            "resource_id": snapshot.id,
            "resource_type": "Snapshot",
            "context_id": self.context_cache[parent_key]
        }]
      with benchmark("Insert Snapshot entries into Revision"):
        engine.execute(models.Revision.__table__.insert(), revision_payload)

      return True

  def create_chunks(self, func, *args, **kwargs):
    """Create chunks if there are too many snapshottable objects."""
    if not self.chunking:
      return func(*args, **kwargs)
    if not len(self.children_objects) > QUEUE_SIZE:
      return func(*args, **kwargs)

    chunks = []
    for parent, children in self.snapshotable_objects.items():
      _children = list(children)
      while _children:
        children_chunk = _children[:QUEUE_SIZE]
        _children = _children[QUEUE_SIZE:]
        chunks += [(parent, children_chunk)]

    first_chunk = chunks[0]
    for chunk in chunks[1:]:
      self._create_bg_task(kwargs["method"], {
          "data": chunk,
          "method": kwargs["method"],
          "operation": func.__name__[1:]
      })

    parent, children = first_chunk
    children = set(children)
    self.parent_objects = {parent}
    self.children_objects = children
    self.snapshotable_objects[parent] = children
    return func(*args, **kwargs)

  def create(self, method):
    """Create snapshots of parent object's neighbourhood per provided rules
    and split in chuncks if there are too many snapshottable objects."""
    return self.create_chunks(self._create, method=method)

  def _create(self, method):
    """Create snapshots of parent objects neighhood and create revisions for
    snapshots."""
    user_id = get_current_user_id()
    revision_id_cache = dict()
    data_payload = list()
    missed_keys = set()
    revision_payload = list()

    with benchmark("Batch CREATE snapshots"):
      revisions = db.session.query(
          models.Revision.id, models.Revision.resource_type,
          models.Revision.resource_id).filter(
          tuple_(
              models.Revision.resource_type,
              models.Revision.resource_id).in_(self.children_objects)
      ).order_by(models.Revision.id.desc()).all()

      for revid, restype, resid in revisions:
        key = (restype, resid)
        if key not in revision_id_cache:
          revision_id_cache[key] = revid

      with benchmark("Create Snapshot payload"):
        for parent_key in self.parent_objects:
          for child_key in self.snapshotable_objects[parent_key]:
            if child_key in revision_id_cache:
              revision_id = revision_id_cache[child_key]
              data_payload += [{
                  "parent_type": parent_key[0],
                  "parent_id": parent_key[1],
                  "child_type": child_key[0],
                  "child_id": child_key[1],
                  "revision_id": revision_id,
                  "modified_by_id": user_id,
                  "context_id": self.context_cache[parent_key]
              }]
            else:
              missed_keys.add(child_key)

      with benchmark("Write Snapshot objects to database"):
        engine = db.engine
        engine.execute(models.Snapshot.__table__.insert(), data_payload)
        db.session.commit()

      # Create Revisions for Snapshots
      with benchmark("Retrieve created snapshots"):
        inserted_snapshots = db.session.query(models.Snapshot).filter(
            tuple_(models.Snapshot.parent_type, models.Snapshot.parent_id).in_(
                self.parent_objects)).all()

      with benchmark("Get Audit creation events"):
        events = self._get_events(method, self.parent_objects)

      with benchmark("Create Revision payload"):
        for isnapshot in inserted_snapshots:
          parent = isnapshot.parent
          parent_key = (parent.type, parent.id)
          event = events[parent_key]
          revision_payload += [{
              "action": "created",
              "event_id": event,
              "content": isnapshot.log_json(),
              "modified_by_id": user_id,
              "resource_id": isnapshot.id,
              "resource_type": "Snapshot",
              "context_id": self.context_cache[parent_key]
          }]

      with benchmark("Write Revision objects to database"):
        engine.execute(models.Revision.__table__.insert(), revision_payload)
        db.session.commit()
    return True


def create_snapshots(objs, method="POST"):
  """Create snapshots of parent objects."""
  generator = SnapshotGenerator()
  if not isinstance(objs, set):
    objs = {objs}
  for obj in objs:
    obj.ff_snapshot_enabled = True
    db.session.add(obj)
    generator.add_parent_object(obj)
  generator.create(method=method)


def update_snapshots(objs, method="PUT"):
  """Update (or create) snapshots of parent objects."""
  generator = SnapshotGenerator()
  if not isinstance(objs, set):
    objs = {objs}
  for obj in objs:
    db.session.add(obj)
    generator.add_parent_object(obj)
  generator.update(method=method)


def register_snapshot_listeners():
  rules = get_rules()

  def create(sender, obj=None, src=None, service=None):
    # TODO REMOVE ON FINAL COMMIT (FEATURE FLAG REMOVAL)
    if src.get("create-snapshots"):
      create_snapshots(obj)

  def update(sender, obj=None, src=None, service=None):
    if src.get("update-snapshots"):
      update_snapshots(obj)

  # Initialize listening on parent objects
  for type_ in rules.rules.keys():
    model = getattr(models.all_models, type_)
    Resource.model_posted_after_commit.connect(create, model, weak=False)
    Resource.model_put_after_commit.connect(update, model, weak=False)
