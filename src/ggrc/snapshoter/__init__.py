# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import collections
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


class Stub(collections.namedtuple("Stub", ["type", "id"])):

  @classmethod
  def from_object(cls, _object):
    return Stub(_object.type, _object.id)

  @classmethod
  def from_dict(cls, _dict):
    return Stub(_dict["type"], _dict["id"])


class Family(collections.namedtuple("Family", ["parent", "children"])):

  def __contains__(self, item):
    pass


Operation = collections.namedtuple(
    "Operation", ["type", "success", "response"])
OperationResponse = collections.namedtuple(
    "OperationResponse", ["success", "response"])

QUEUE_SIZE = 1000


def create_snapshot_dict(parent, child, revision_id, user_id, context_id):
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
  return {
      "source_type": source.type,
      "source_id": source.id,
      "destination_type": destination.type,
      "destination_id": destination.id,
      "modified_by_id": user_id,
      "context_id": context_id,
  }


def create_relationship_revision_dict(action, event, relationship,
                                      user_id, context_id):
  return {
      "action": action,
      "event_id": event,
      "content": create_relationship_log(relationship),
      "modified_by_id": user_id,
      "resource_id": relationship[0],
      "resource_type": "Relationship",
      "context_id": context_id
  }


def get_snapshots(objects):
  return db.session.query(
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
  ).filter(
      tuple_(
          models.Snapshot.parent_type,
          models.Snapshot.parent_id,
          models.Snapshot.child_type,
          models.Snapshot.child_id
      ).in_({(parent.type, parent.id, child.type, child.id)
             for parent, child in objects}))


def get_event(_object, action):
  """Retrieve the last event for parent objects that performed
  PUT/POST/IMPORT/Event.action action."""
  with benchmark("Snapshot.get_events"):
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


def create_snapshot_log(snapshot):
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


def get_revisions(pairs, revisions, filters=None):
  revision_id_cache = dict()

  child_stubs = {child for parent, child in pairs}
  with benchmark("Snapshot.get_revisions"):
    with benchmark("Snapshot.get_revisions.retrieve revisions"):
      query = db.session.query(
          models.Revision.id,
          models.Revision.resource_type,
          models.Revision.resource_id).filter(
          tuple_(
              models.Revision.resource_type,
              models.Revision.resource_id).in_(child_stubs)
      ).order_by(models.Revision.id.desc())
      if filters:
        for filter in filters:
          query = query.filter(filter)

      with benchmark("Snapshot.get_revisions.create child -> parents cache"):
        parents_cache = collections.defaultdict(set)
        for parent, child in pairs:
          parents_cache[child].add(parent)

    with benchmark("Snapshot.get_revisions.create revision_id cache"):
      for revid, restype, resid in query:
        child = Stub(restype, resid)
        for parent in parents_cache[child]:
          key = (parent, child)
          if key in revisions:
            if revid == revisions[key]:
              revision_id_cache[key] = revid
          else:
            if key not in revision_id_cache:
              revision_id_cache[key] = revid
    return revision_id_cache


def get_relationships(relationships):
  with benchmark("Snapshot.get_relationships"):
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


class SnapshotGenerator(object):
  """Geneate snapshots per rules of all connected objects"""

  def __init__(self, chunking=True, dry_run=False):
    self._RULES = get_rules()
    self.OPERATION_HANDLERS = {
        "create": self._create,
        "update": self._update
    }

    self.parents = set()
    self.children = set()
    self.snapshots = dict()
    self.context_cache = dict()
    self.chunking = chunking

  def add_parent(self, obj):
    """Add parent object and automatically scan neighbourhood for snapshottable
    objects."""
    with benchmark("Snapshot.add_parent_object"):
      # key = (obj.type, obj.id)
      key = Stub.from_object(obj)
      if key not in self.parents:
        with benchmark("Snapshot.add_parent_object.add object"):
          objs = self._get_snapshottable_objects(obj)
          self.parents.add(key)
          self.context_cache[key] = obj.context_id
          self.children = self.children | objs
          self.snapshots[key] = objs
      return self.parents

  def add_family(self, parent, children):
    """Directly add parent object and children that should be snapshotted."""
    _type, _id = parent
    model = getattr(models, _type)
    parent_object = db.session.query(model).filter(model.id == _id).one()
    self.parents.add(parent)
    self.snapshots[parent] = children
    self.children = children
    self.context_cache[parent] = parent_object.context_id

  def _create_bg_task(self, method, chunk):
    """Create background task"""
    return create_task(
        name="{}-SNAPSHOTS-".format(method),
        url="/_process_snapshots",
        queued_callback=None, parameters=json.dumps(chunk))

  def _fetch_neighbourhood(self, parent_object, objects):
    with benchmark("Snapshot._fetch_object_neighbourhood"):
      query_pairs = set()
      rules = self._RULES.rules[parent_object.type]["snd"]

      for obj in objects:
        for snd_obj in rules:
          query_pairs.add((obj.type, obj.id, snd_obj))

      columns = db.session.query(
          models.Relationship.source_type,
          models.Relationship.source_id,
          models.Relationship.destination_type,
          models.Relationship.destination_id)

      relationships = columns.filter(
          tuple_(
              models.Relationship.destination_type,
              models.Relationship.destination_id,
              models.Relationship.source_type,
          ).in_(query_pairs)).union(
          columns.filter(tuple_(
              models.Relationship.source_type,
              models.Relationship.source_id,
              models.Relationship.destination_type,
          ).in_(query_pairs)))

      neighbourhood = set()
      for (stype, sid, dtype, did) in relationships:
        source = Stub(stype, sid)
        destination = Stub(dtype, did)

        if source in objects:
          neighbourhood.add(destination)
        else:
          neighbourhood.add(source)
      return neighbourhood

  def _get_snapshottable_objects(self, obj):
    """Get snapshottable objects from parent object's neighbourhood."""
    with benchmark("Snapshot._get_snapshotable_objects"):
      object_rules = self._RULES.rules[obj.type]

      with benchmark("Snapshot._get_snapshotable_objects.related_mappings"):
        related_mappings = obj.related_objects({
            rule for rule in object_rules["fst"]
            if isinstance(rule, basestring)})

      with benchmark("Snapshot._get_snapshotable_objects.direct mappings"):
        direct_mappings = {getattr(obj, rule.name)
                           for rule in object_rules["fst"]
                           if isinstance(rule, Attr)}

      related_objects = {Stub.from_object(obj)
                         for obj in related_mappings | direct_mappings}

    with benchmark("Snapshot._get_snapshotable_objects.get second degree"):
      return self._fetch_neighbourhood(obj, related_objects)

  def update(self, event, revisions, filter=None):
    """Update parent object's snapshots and split in chunks if there are too
    many of them."""
    _, for_update = self.analyze()
    return self._update(for_update=for_update, event=event,
                        revisions=revisions, _filter=filter)

  def _update(self, for_update, event, revisions, _filter):
    """Update (or create) parent objects' snapshots and create revisions for
    them."""
    user_id = get_current_user_id()
    event_id = event.id
    engine = db.engine
    missed_keys = set()
    revision_id_cache = dict()
    snapshot_cache = dict()
    modified_snapshot_keys = set()
    data_payload_update = list()
    revision_payload = list()

    with benchmark("Snapshot._update.filter"):
      for_update = filter(_filter, for_update)

    with benchmark("Snapshot._update.get existing snapshots"):
      existing_snapshots = db.session.query(
          models.Snapshot.id,
          models.Snapshot.parent_type,
          models.Snapshot.parent_id,
          models.Snapshot.child_type,
          models.Snapshot.child_id,
          models.Snapshot.revision_id,
      ).filter(tuple_(
          models.Snapshot.parent_type, models.Snapshot.parent_id,
          models.Snapshot.child_type, models.Snapshot.child_id
      ).in_({(parent.type, parent.id, child.type, child.id)
             for parent, child in for_update}))

      for sid, ptype, pid, ctype, cid, revid in existing_snapshots:
        parent = Stub(ptype, pid)
        child = Stub(ctype, cid)
        snapshot_cache[child] = [sid, revid, parent]

    with benchmark("Batch UPDATE snapshots"):
      with benchmark("Retrieve latest revisions"):
        revision_id_cache = get_revisions(
            for_update,
            filters=[models.Revision.action.in_(["created", "modified"])],
            revisions=revisions)

      with benchmark("Build models.Snapshot payload"):
        for parent, child in for_update:
          key = (parent, child)
          if key in revision_id_cache:
            sid, revid, _ = snapshot_cache[child]
            latest_rev = revision_id_cache[key]
            if revid != latest_rev:
              modified_snapshot_keys.add(key)
              data_payload_update += [{
                  "_id": sid,
                  "_revision_id": latest_rev,
                  "_modified_by_id": user_id
              }]
          else:
            missed_keys.add(key)

      with benchmark("Snapshot._update.write snapshots to database"):
        update_sql = models.Snapshot.__table__.update().where(
            models.Snapshot.id == bindparam("_id")).values(
            revision_id=bindparam("_revision_id"),
            modified_by_id=bindparam("_modified_by_id"))
        if data_payload_update:
          engine.execute(update_sql, data_payload_update)
        db.session.commit()

      # Create revisions for snapshots
      touched_snapshots = {(ptype, pid, ctype, cid)
                           for ptype, pid in self.snapshots
                           for ctype, cid in self.snapshots[
                           (ptype, pid)]}
      snapshots = db.session.query(models.Snapshot).filter(
          tuple_(
              models.Snapshot.parent_type, models.Snapshot.parent_id,
              models.Snapshot.child_type, models.Snapshot.child_id).in_(
                  touched_snapshots)).all()

      snapshot_ids = {sh.id for sh in snapshots}
      snapshots = {sh.id: sh for sh in snapshots}

      for snapshot in snapshots.values():
        parent = snapshot.parent
        parent_key = (parent.type, parent.id)
        revision_payload += [{
            "action": "modified",
            "event_id": event_id,
            "content": snapshot.log_json(),
            "modified_by_id": user_id,
            "resource_id": snapshot.id,
            "resource_type": "Snapshot",
            "context_id": self.context_cache[parent_key]
        }]
      with benchmark("Insert Snapshot entries into Revision"):
        engine.execute(models.Revision.__table__.insert(), revision_payload)
        db.session.commit()

      return OperationResponse(True, for_update)

  def create_chunks(self, func, *args, **kwargs):
    """Create chunks if there are too many snapshottable objects."""
    with benchmark("Snapshot.create_chunks"):
      if not self.chunking:
        return func(*args, **kwargs)
      if not len(self.children) > QUEUE_SIZE:
        return func(*args, **kwargs)

      chunks = []
      for parent, children in self.snapshots.items():
        _children = list(children)
        while _children:
          children_chunk = _children[:QUEUE_SIZE]
          _children = _children[QUEUE_SIZE:]
          chunks += [(parent, children_chunk)]

      first_chunk = chunks[0]
      with benchmark("Snapshot.create_chunks.create bg tasks"):
        for chunk in chunks[1:]:
          self._create_bg_task(kwargs["method"], {
              "data": chunk,
              "method": kwargs["method"],
              "operation": func.__name__[1:]
          })

      parent, children = first_chunk
      children = set(children)
      self.parents = {parent}
      self.children = children
      self.snapshots[parent] = children
      return func(*args, **kwargs)

  def analyze(self):
    query = set(db.session.query(
        models.Snapshot.parent_type,
        models.Snapshot.parent_id,
        models.Snapshot.child_type,
        models.Snapshot.child_id,
    ).filter(tuple_(
        models.Snapshot.parent_type, models.Snapshot.parent_id
    ).in_(self.parents)))

    existing_scope = {(Stub._make(fields[0:2]), Stub._make(fields[2:4]))
                      for fields in query}

    full_scope = {(parent, child)
                  for parent, children in self.snapshots.items()
                  for child in children}

    for_update = existing_scope
    for_create = full_scope - existing_scope

    return for_create, for_update

  def upsert(self, event, revisions, filter):
    return self._upsert(event=event, revisions=revisions, filter=filter)

  def _upsert(self, event, revisions, filter):
    for_create, for_update = self.analyze()

    if for_update:
      update = self._update(
          for_update=for_update, event=event, revisions=revisions,
          _filter=filter)
    if for_create:
      create = self._create(for_create=for_create, event=event,
                            revisions=revisions, _filter=filter)

  def create(self, event, revisions, filter=None):
    """Create snapshots of parent object's neighbourhood per provided rules
    and split in chuncks if there are too many snapshottable objects."""
    # return self.create_chunks(self._create, method=method)
    for_create, _ = self.analyze()
    return self._create(
        for_create=for_create, event=event,
        revisions=revisions, _filter=filter)

  def _create(self, for_create, event, revisions, _filter):
    """Create snapshots of parent objects neighhood and create revisions for
    snapshots."""
    with benchmark("Snapshot._create init"):
      user_id = get_current_user_id()
      missed_keys = set()
      data_payload = list()
      revision_payload = list()
      relationship_payload = list()
      event_id = event.id

    with benchmark("Snapshot._create.filter"):
      for_create = filter(_filter, for_create)
    with benchmark("Snapshot._create main"):
      with benchmark("Snapshot._create._get_revisions"):
        revision_id_cache = get_revisions(for_create, revisions)

      with benchmark("Snapshot._create.create payload"):
        for parent, child in for_create:
          key = (parent, child)
          if key in revision_id_cache:
            revision_id = revision_id_cache[key]
            context_id = self.context_cache[parent]
            data = create_snapshot_dict(parent, child,
                                        revision_id, user_id, context_id)
            data_payload += [data]
          else:
            # TODO Remove before production - there should never be a missing
            # TODO revision
            missed_keys.add(key)

      with benchmark("Snapshot._create.write to database"):
        engine = db.engine
        engine.execute(models.Snapshot.__table__.insert(), data_payload)
        db.session.commit()

      with benchmark("Snapshot._create.retrieve inserted snapshots"):
        snapshots = get_snapshots(for_create)

      with benchmark("Snapshot._create.create base object -> snapshot rels"):
        for snapshot in snapshots:
          base_object = Stub._make(snapshot[6:8])
          snapshot_object = Stub("Snapshot", snapshot[0])
          relationship = create_relationship_dict(base_object, snapshot_object,
                                                  user_id, snapshot[1])
          relationship_payload += [relationship]

      with benchmark("Snapshot._create.write relationships to database"):
        engine.execute(models.Relationship.__table__.insert(),
                       relationship_payload)
        db.session.commit()

      with benchmark("Snapshot._create.get created relationships"):
        created_relationships = {
            (rel["source_type"], rel["source_id"],
             rel["destination_type"], rel["destination_id"])
            for rel in relationship_payload}
        relationships = get_relationships(created_relationships)

      with benchmark("Snapshot._create.create revision payload"):
        with benchmark("Snapshot._create.create snapshots revision payload"):
          for snapshot in snapshots:
            parent = Stub._make(snapshot[4:6])
            context_id = self.context_cache[parent]
            data = create_snapshot_revision_dict("created", event_id, snapshot,
                                                 user_id, context_id)
            revision_payload += [data]

        with benchmark("Snapshot._create.create rel revision payload"):
          snapshot_parents = {child: parent for parent, child in for_create}
          for relationship in relationships:
            obj = Stub._make(relationship[4:6])
            parent = snapshot_parents[obj]
            context_id = self.context_cache[parent]
            data = create_relationship_revision_dict(
                "created", event_id, relationship, user_id, context_id)
            revision_payload += [data]

      with benchmark("Snapshot._create.write revisions to database"):
        engine.execute(models.Revision.__table__.insert(), revision_payload)
        db.session.commit()
    return OperationResponse(True, for_create)


def create_snapshots(objs, event, revisions=set(), filter=None):
  """Create snapshots of parent objects."""
  with benchmark("Snapshot.create_snapshots"):
    with benchmark("Snapshot.create_snapshots.init"):
      generator = SnapshotGenerator()
      if not isinstance(objs, set):
        objs = {objs}
      for obj in objs:
        obj.ff_snapshot_enabled = True
        db.session.add(obj)
        with benchmark("Snapshot.create_snapshots.add_parent_objects"):
          generator.add_parent(obj)
    with benchmark("Snapshot.create_snapshots.create"):
      generator.create(event=event, revisions=revisions, filter=filter)


def update_snapshots(objs, event, revisions=set(), filter=None):
  """Update (or create) snapshots of parent objects."""
  with benchmark("Snapshot.update_snapshots"):
    generator = SnapshotGenerator()
    if not isinstance(objs, set):
      objs = {objs}
    for obj in objs:
      db.session.add(obj)
      generator.add_parent(obj)
    generator.upsert(event=event, revisions=revisions, filter=filter)


def update_snapshot(snapshot, event, revisions=set(), filter=None):
  """Update individual snapshot to the latest version"""
  with benchmark("Snapshot.individual update"):
    generator = SnapshotGenerator()
    parent = Stub.from_object(snapshot.parent)
    child = Stub(snapshot.child_type, snapshot.child_id)
    generator.add_family(parent, {child})
    generator.update(event=event, revisions=revisions,
                     filter=lambda x: x in {(parent, child)})


def register_snapshot_listeners():
  rules = get_rules()

  def create(sender, obj=None, src=None, service=None):
    # TODO REMOVE ON FINAL COMMIT (FEATURE FLAG REMOVAL)
    snapshot_settings = src.get("snapshots")
    if snapshot_settings:
      if snapshot_settings["operation"] == "create":
        with benchmark("Snapshot.register_snapshot_listeners.create"):
          event = get_event(obj, "POST")
        create_snapshots(obj, event)

  def update_all(sender, obj=None, src=None, service=None):
    snapshot_settings = src.get("snapshots")
    if snapshot_settings:
      if snapshot_settings["operation"] == "upsert":
        revisions = {
            (Stub.from_dict(revision["parent"]),
             Stub.from_dict(revision["child"])): revision["revision_id"]
            for revision in snapshot_settings.get("revisions", {})}
        with benchmark("Snapshot.register_snapshot_listeners.create"):
          event = get_event(obj, "PUT")
        update_snapshots(obj, event, revisions=revisions)

  def update_one(sender, obj=None, src=None, service=None):
    event = models.Event(
        modified_by_id=get_current_user_id(),
        action="PUT",
        resource_id=obj.id,
        resource_type=obj.type,
        context_id=obj.context_id)

    db.session.add(event)
    # Because we need event's ID
    db.session.flush()

    if src.get("update"):
      update_snapshot(obj, event)

  # Initialize listening on parent objects
  for type_ in rules.rules.keys():
    model = getattr(models.all_models, type_)
    Resource.model_posted_after_commit.connect(create, model, weak=False)
    Resource.model_put_after_commit.connect(update_all, model, weak=False)

  Resource.model_put.connect(update_one, models.Snapshot, weak=False)
