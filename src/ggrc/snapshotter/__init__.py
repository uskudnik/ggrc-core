# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import json

from sqlalchemy.sql.expression import tuple_
from sqlalchemy.sql.expression import bindparam

from ggrc import db
from ggrc import models
from ggrc.models.background_task import create_task
from ggrc.login import get_current_user_id
from ggrc.utils import benchmark

from ggrc.snapshotter.datastructures import Attr
from ggrc.snapshotter.datastructures import Pair
from ggrc.snapshotter.datastructures import Stub
from ggrc.snapshotter.datastructures import OperationResponse
from ggrc.snapshotter.helpers import create_relationship_dict
from ggrc.snapshotter.helpers import create_relationship_revision_dict
from ggrc.snapshotter.helpers import create_snapshot_dict
from ggrc.snapshotter.helpers import create_snapshot_revision_dict
from ggrc.snapshotter.helpers import create_dry_run_response
from ggrc.snapshotter.helpers import get_relationships
from ggrc.snapshotter.helpers import get_revisions
from ggrc.snapshotter.helpers import get_snapshots

from ggrc.snapshotter.rules import get_rules


QUEUE_SIZE = 100000


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
    self.dry_run = dry_run

  def add_parent(self, obj):
    """Add parent object and automatically scan neighbourhood for snapshottable
    objects."""
    with benchmark("Snapshot.add_parent_object"):
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

      with benchmark("Snapshot._get_snapshotable_objects.fetch neighbourhood"):
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
    with benchmark("Snapshot._update"):
      user_id = get_current_user_id()
      event_id = event.id
      engine = db.engine
      missed_keys = set()
      snapshot_cache = dict()
      modified_snapshot_keys = set()
      data_payload_update = list()
      revision_payload = list()

      with benchmark("Snapshot._update.filter"):
        for_update = filter(_filter, for_update)

      with benchmark("Snapshot._update.get existing snapshots"):
        existing_snapshots = db.session.query(
            models.Snapshot.id,
            models.Snapshot.revision_id,
            models.Snapshot.parent_type,
            models.Snapshot.parent_id,
            models.Snapshot.child_type,
            models.Snapshot.child_id,
        ).filter(tuple_(
            models.Snapshot.parent_type, models.Snapshot.parent_id,
            models.Snapshot.child_type, models.Snapshot.child_id
        ).in_({pair.to_4tuple() for pair in for_update}))

        for es in existing_snapshots:
          sid, rev_id, pair_tuple = es[0], es[1], es[2:]
          pair = Pair.from_4tuple(pair_tuple)
          snapshot_cache[pair] = (sid, rev_id)

      with benchmark("Snapshot._update.retrieve latest revisions"):
        revision_id_cache = get_revisions(
            for_update,
            filters=[models.Revision.action.in_(["created", "modified"])],
            revisions=revisions)

      if self.dry_run:
        old_revisions = {pair: values[1]
                         for pair, values in snapshot_cache.items()}
        response = create_dry_run_response(
            for_update, old_revisions, revision_id_cache)
        return OperationResponse("update", True, response, {
            "dry-run": True
        })

      with benchmark("Snapshot._update.build snapshot payload"):
        for key in for_update:
          if key in revision_id_cache:
            sid, rev_id = snapshot_cache[key]
            latest_rev = revision_id_cache[key]
            if rev_id != latest_rev:
              modified_snapshot_keys.add(key)
              data_payload_update += [{
                  "_id": sid,
                  "_revision_id": latest_rev,
                  "_modified_by_id": user_id
              }]
          else:
            missed_keys.add(key)

      if not modified_snapshot_keys:
        return OperationResponse("update", True, set(), None)

      with benchmark("Snapshot._update.write snapshots to database"):
        update_sql = models.Snapshot.__table__.update().where(
            models.Snapshot.id == bindparam("_id")).values(
            revision_id=bindparam("_revision_id"),
            modified_by_id=bindparam("_modified_by_id"))
        if data_payload_update:
          engine.execute(update_sql, data_payload_update)
        db.session.commit()

      with benchmark("Snapshot._update.retrieve inserted snapshots"):
        snapshots = get_snapshots(modified_snapshot_keys)

      with benchmark("Snapshot._update.create snapshots revision payload"):
        for snapshot in snapshots:
          parent = Stub.from_tuple(snapshot, 4, 5)
          context_id = self.context_cache[parent]
          data = create_snapshot_revision_dict("modified", event_id, snapshot,
                                               user_id, context_id)
          revision_payload += [data]

      with benchmark("Insert Snapshot entries into Revision"):
        engine.execute(models.Revision.__table__.insert(), revision_payload)
        db.session.commit()
      return OperationResponse("update", True, for_update, None)

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

    existing_scope = {Pair.from_4tuple(fields) for fields in query}

    full_scope = {Pair(parent, child)
                  for parent, children in self.snapshots.items()
                  for child in children}

    for_update = existing_scope
    for_create = full_scope - existing_scope

    return for_create, for_update

  def upsert(self, event, revisions, filter):
    return self._upsert(event=event, revisions=revisions, filter=filter)

  def _upsert(self, event, revisions, filter):
    for_create, for_update = self.analyze()
    create, update = None, None

    if for_update:
      update = self._update(
          for_update=for_update, event=event, revisions=revisions,
          _filter=filter)
    if for_create:
      create = self._create(for_create=for_create, event=event,
                            revisions=revisions, _filter=filter)

    return OperationResponse("upsert", True, {
        "create": create,
        "update": update
    }, {
        "dry-run": self.dry_run
    })

  def create(self, event, revisions, filter=None):
    """Create snapshots of parent object's neighbourhood per provided rules
    and split in chuncks if there are too many snapshottable objects."""
    for_create, _ = self.analyze()
    return self._create(
        for_create=for_create, event=event,
        revisions=revisions, _filter=filter)

  def _create(self, for_create, event, revisions, _filter):
    """Create snapshots of parent objects neighhood and create revisions for
    snapshots."""
    with benchmark("Snapshot._create"):
      with benchmark("Snapshot._create init"):
        user_id = get_current_user_id()
        missed_keys = set()
        data_payload = list()
        revision_payload = list()
        relationship_payload = list()
        event_id = event.id

      with benchmark("Snapshot._create.filter"):
        for_create = filter(_filter, for_create)
      with benchmark("Snapshot._create._get_revisions"):
        revision_id_cache = get_revisions(for_create, revisions)

      if self.dry_run:
        response = create_dry_run_response(for_create, dict(),
                                           revision_id_cache)
        return OperationResponse("create", True, response, {
            "dry-run": True
        })

      with benchmark("Snapshot._create.create payload"):
        for pair in for_create:
          if pair in revision_id_cache:
            revision_id = revision_id_cache[pair]
            context_id = self.context_cache[pair.parent]
            data = create_snapshot_dict(pair, revision_id, user_id, context_id)
            data_payload += [data]
          else:
            missed_keys.add(pair)

      with benchmark("Snapshot._create.write to database"):
        engine = db.engine
        engine.execute(models.Snapshot.__table__.insert(), data_payload)
        db.session.commit()

      with benchmark("Snapshot._create.retrieve inserted snapshots"):
        snapshots = get_snapshots(for_create)

      with benchmark("Snapshot._create.create base object -> snapshot rels"):
        for snapshot in snapshots:
          base_object = Stub.from_tuple(snapshot, 6, 7)
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
            parent = Stub.from_tuple(snapshot, 4, 5)
            context_id = self.context_cache[parent]
            data = create_snapshot_revision_dict("created", event_id, snapshot,
                                                 user_id, context_id)
            revision_payload += [data]

        with benchmark("Snapshot._create.create rel revision payload"):
          snapshot_parents = {pair.child: pair.parent for pair in for_create}
          for relationship in relationships:
            obj = Stub.from_tuple(relationship, 4, 5)
            parent = snapshot_parents[obj]
            context_id = self.context_cache[parent]
            data = create_relationship_revision_dict(
                "created", event_id, relationship, user_id, context_id)
            revision_payload += [data]

      with benchmark("Snapshot._create.write revisions to database"):
        engine.execute(models.Revision.__table__.insert(), revision_payload)
        db.session.commit()
      return OperationResponse("create", True, for_create, None)


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
