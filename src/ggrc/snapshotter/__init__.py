# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Main snapshotter module

Snapshotter creates an immutable scope around an object (e.g. Audit) where
snapshot object represent a join between parent object (Audit),
child object (e.g. Control, Regulation, ...) and a particular revision.
"""


from sqlalchemy.sql.expression import tuple_
from sqlalchemy.sql.expression import bindparam

from ggrc import db
from ggrc import models
from ggrc.models.reflection import AttributeInfo
from ggrc.login import get_current_user_id
from ggrc.utils import benchmark

from ggrc.snapshotter.datastructures import Attr
from ggrc.snapshotter.datastructures import Pair
from ggrc.snapshotter.datastructures import Stub
from ggrc.snapshotter.datastructures import OperationResponse
from ggrc.snapshotter.helpers import create_relationship_dict
from ggrc.snapshotter.helpers import create_relationship_revision_dict
from ggrc.snapshotter.helpers import create_snapshot_dict
from ggrc.snapshotter.helpers import create_bg_task
from ggrc.snapshotter.helpers import create_snapshot_revision_dict
from ggrc.snapshotter.helpers import get_relationships
from ggrc.snapshotter.helpers import get_revisions
from ggrc.snapshotter.helpers import get_snapshots
from ggrc.snapshotter.indexer import reindex_pairs

from ggrc.snapshotter.rules import get_rules


QUEUE_SIZE = 100000


class SnapshotGenerator(object):
  """Geneate snapshots per rules of all connected objects"""

  def __init__(self, dry_run, chunking=True):
    self.rules = get_rules()

    self.parents = set()
    self.children = set()
    self.snapshots = dict()
    self.context_cache = dict()
    self.chunking = chunking
    self.dry_run = dry_run

  def add_parent(self, obj):
    """Add parent object and automatically scan neighborhood for snapshottable
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

  def _fetch_neighborhood(self, parent_object, objects):
    with benchmark("Snapshot._fetch_object_neighborhood"):
      query_pairs = set()

      for obj in objects:
        for snd_obj in self.rules.rules[parent_object.type]["snd"]:
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

      neighborhood = set()
      for (stype, sid, dtype, did) in relationships:
        source = Stub(stype, sid)
        destination = Stub(dtype, did)

        if source in objects:
          neighborhood.add(destination)
        else:
          neighborhood.add(source)
      return neighborhood

  def _get_snapshottable_objects(self, obj):
    """Get snapshottable objects from parent object's neighborhood."""
    with benchmark("Snapshot._get_snapshotable_objects"):
      object_rules = self.rules.rules[obj.type]

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

      with benchmark("Snapshot._get_snapshotable_objects.fetch neighborhood"):
        return self._fetch_neighborhood(obj, related_objects)

  def update(self, event, revisions, _filter=None):
    """Update parent object's snapshots and split in chunks if there are too
    many of them."""
    _, for_update = self.analyze()
    result = self._update(for_update=for_update, event=event,
                          revisions=revisions, _filter=_filter)
    updated = result.response
    if not self.dry_run:
      reindex_pairs(updated)
    return result

  def _update(self, for_update, event, revisions, _filter):
    """Update (or create) parent objects' snapshots and create revisions for
    them.

    Args:
      event: A ggrc.models.Event instance
      revisions: A set of tuples of pairs with revisions to which it should
        either create or update a snapshot of that particular audit
      _filter: Callable that should return True if it should be updated
    Returns:
      OperationResponse
    """
    # pylint: disable=too-many-locals
    with benchmark("Snapshot._update"):
      user_id = get_current_user_id()
      missed_keys = set()
      snapshot_cache = dict()
      modified_snapshot_keys = set()
      data_payload_update = list()
      revision_payload = list()
      response_data = dict()

      if self.dry_run and event is None:
        event_id = 0
      else:
        event_id = event.id

      with benchmark("Snapshot._update.filter"):
        if _filter:
          for_update = {elem for elem in for_update if _filter(elem)}

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

        for esnap in existing_snapshots:
          sid, rev_id, pair_tuple = esnap[0], esnap[1], esnap[2:]
          pair = Pair.from_4tuple(pair_tuple)
          snapshot_cache[pair] = (sid, rev_id)

      with benchmark("Snapshot._update.retrieve latest revisions"):
        revision_id_cache = get_revisions(
            for_update,
            filters=[models.Revision.action.in_(["created", "modified"])],
            revisions=revisions)

      response_data["revisions"] = {
          "old": {pair: values[1] for pair, values in snapshot_cache.items()},
          "new": revision_id_cache
      }

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
        return OperationResponse("update", True, set(), response_data)

      with benchmark("Snapshot._update.write snapshots to database"):
        update_sql = models.Snapshot.__table__.update().where(
            models.Snapshot.id == bindparam("_id")).values(
            revision_id=bindparam("_revision_id"),
            modified_by_id=bindparam("_modified_by_id"))
        self._execute(update_sql, data_payload_update)

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
        self._execute(models.Revision.__table__.insert(), revision_payload)
      return OperationResponse("update", True, for_update, response_data)

  def create_chunks(self, func, *args, **kwargs):
    """Create chunks if there are too many snapshottable objects."""
    with benchmark("Snapshot.create_chunks"):
      if not self.chunking:
        return func(*args, **kwargs)
      if len(self.children) <= QUEUE_SIZE:
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
          create_bg_task(kwargs["method"], {
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
    """Analyze which snapshots need to be updated and which created"""
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

  def upsert(self, event, revisions, _filter):
    return self._upsert(event=event, revisions=revisions, _filter=_filter)

  def _upsert(self, event, revisions, _filter):
    """Update and (if needed) create snapshots

    Args:
      event: A ggrc.models.Event instance
      revisions: A set of tuples of pairs with revisions to which it should
        either create or update a snapshot of that particular audit
      _filter: Callable that should return True if it should be updated
    Returns:
      OperationResponse
    """
    for_create, for_update = self.analyze()
    create, update = None, None
    created, updated = set(), set()

    if for_update:
      update = self._update(
          for_update=for_update, event=event, revisions=revisions,
          _filter=_filter)
      updated = update.response
    if for_create:
      create = self._create(for_create=for_create, event=event,
                            revisions=revisions, _filter=_filter)
      created = create.response

    to_reindex = updated | created
    if not self.dry_run:
      reindex_pairs(to_reindex)
    return OperationResponse("upsert", True, {
        "create": create,
        "update": update
    }, {
        "dry-run": self.dry_run
    })

  def _execute(self, operation, data):
    """Execute bulk operation on data if not in dry mode

    Args:
      operation: sqlalchemy operation
      data: a list of dictionaries with keys representing column names and
        values to insert with operation
    Returns:
      True if successful.
    """
    if data and not self.dry_run:
      engine = db.engine
      engine.execute(operation, data)
      db.session.commit()
    return True

  def create(self, event, revisions, _filter=None):
    """Create snapshots of parent object's neighborhood per provided rules
    and split in chuncks if there are too many snapshottable objects."""
    for_create, _ = self.analyze()
    result = self._create(
        for_create=for_create, event=event,
        revisions=revisions, _filter=_filter)
    created = result.response
    if not self.dry_run:
      reindex_pairs(created)
    return result

  def _create(self, for_create, event, revisions, _filter):
    """Create snapshots of parent objects neighhood and create revisions for
    snapshots.

    Args:
      event: A ggrc.models.Event instance
      revisions: A set of tuples of pairs with revisions to which it should
        either create or update a snapshot of that particular audit
      _filter: Callable that should return True if it should be updated
    Returns:
      OperationResponse
    """
    # pylint: disable=too-many-locals,too-many-statements
    with benchmark("Snapshot._create"):
      with benchmark("Snapshot._create init"):
        user_id = get_current_user_id()
        missed_keys = set()
        data_payload = list()
        revision_payload = list()
        relationship_payload = list()
        response_data = dict()

        if self.dry_run and event is None:
          event_id = 0
        else:
          event_id = event.id

      with benchmark("Snapshot._create.filter"):
        if _filter:
          for_create = {elem for elem in for_create if _filter(elem)}

      with benchmark("Snapshot._create._get_revisions"):
        revision_id_cache = get_revisions(for_create, revisions)

      response_data["revisions"] = revision_id_cache

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
        self._execute(
            models.Snapshot.__table__.insert(),
            data_payload)

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
        self._execute(models.Relationship.__table__.insert(),
                      relationship_payload)

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
        self._execute(models.Revision.__table__.insert(), revision_payload)
      return OperationResponse("create", True, for_create, response_data)


def create_snapshots(objs, event, revisions=None, _filter=None, dry_run=False):
  """Create snapshots of parent objects."""
  # pylint: disable=unused-argument
  if not revisions:
    revisions = set()

  with benchmark("Snapshot.create_snapshots"):
    with benchmark("Snapshot.create_snapshots.init"):
      generator = SnapshotGenerator(dry_run)
      if not isinstance(objs, set):
        objs = {objs}
      for obj in objs:
        obj.ff_snapshot_enabled = True
        db.session.add(obj)
        with benchmark("Snapshot.create_snapshots.add_parent_objects"):
          generator.add_parent(obj)
    with benchmark("Snapshot.create_snapshots.create"):
      return generator.create(event=event,
                              revisions=revisions,
                              _filter=_filter)


def upsert_snapshots(objs, event, revisions=None, _filter=None, dry_run=False):
  """Update (and create if needed) snapshots of parent objects."""
  # pylint: disable=unused-argument
  if not revisions:
    revisions = set()

  with benchmark("Snapshot.update_snapshots"):
    generator = SnapshotGenerator(dry_run)
    if not isinstance(objs, set):
      objs = {objs}
    for obj in objs:
      db.session.add(obj)
      generator.add_parent(obj)
    return generator.upsert(event=event, revisions=revisions, _filter=_filter)


def update_snapshot(snapshot, event, revisions=None, _filter=None,
                    dry_run=False):
  """Update individual snapshot to the latest version"""

  if not revisions:
    revisions = set()

  if not _filter:
    def _filter(item):  # pylint: disable=function-redefined
      return item in {(parent, child)}

  with benchmark("Snapshot.individual update"):
    generator = SnapshotGenerator(dry_run)
    parent = Stub.from_object(snapshot.parent)
    child = Stub(snapshot.child_type, snapshot.child_id)
    generator.add_family(parent, {child})
    return generator.update(event=event, revisions=revisions,
                            _filter=_filter)
