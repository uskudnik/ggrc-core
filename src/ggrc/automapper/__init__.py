# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from datetime import datetime
import collections
import logging

from sqlalchemy.sql.expression import tuple_
from ggrc import db
from ggrc import models
from ggrc.automapper.rules import rules
from ggrc.login import get_current_user
from ggrc.models.audit import Audit
from ggrc.models.relationship import Relationship
from ggrc.models.request import Request
from ggrc.rbac.permissions import is_allowed_update
from ggrc.services.common import Resource
from ggrc.utils import benchmark, with_nop


class Stub(collections.namedtuple("Stub", ["type", "id"])):

  @classmethod
  def from_source(cls, relationship):
    return Stub(relationship.source_type, relationship.source_id)

  @classmethod
  def from_destination(cls, relationship):
    return Stub(relationship.destination_type, relationship.destination_id)


class AutomapperGenerator(object):

  def __init__(self, use_benchmark=True):
    self.processed = set()
    self.queue = set()
    self.cache = collections.defaultdict(set)
    self.instance_cache = {}
    self.auto_mappings = set()
    if use_benchmark:
      self.benchmark = benchmark
    else:
      self.benchmark = with_nop

  def related(self, obj):
    if obj in self.cache:
      return self.cache[obj]
    # Pre-fetch neighborhood for enqueued object since we're gonna need that
    # results in a few steps. This drastically reduces number of queries.
    stubs = {s for rel in self.queue for s in rel}
    stubs.add(obj)
    # Union is here to convince mysql to use two separate indices and
    # merge te results. Just using `or` results in a full-table scan
    # Manual column list avoids loading the full object which would also try to
    # load related objects
    cols = db.session.query(
        Relationship.source_type, Relationship.source_id,
        Relationship.destination_type, Relationship.destination_id)
    relationships = cols.filter(
        tuple_(Relationship.source_type, Relationship.source_id).in_(
            [(s.type, s.id) for s in stubs]
        )
    ).union_all(
        cols.filter(
            tuple_(Relationship.destination_type,
                   Relationship.destination_id).in_(
                       [(s.type, s.id) for s in stubs]))
    ).all()
    batch_requests = collections.defaultdict(set)
    for (src_type, src_id, dst_type, dst_id) in relationships:
      src = Stub(src_type, src_id)
      dst = Stub(dst_type, dst_id)
      # only store a neighbor if we queried for it since this way we know
      # we'll be storing complete neighborhood by the end of the loop
      batch_requests[src_type].add(src_id)
      batch_requests[dst_type].add(dst_id)
      if src in stubs:
        self.cache[src].add(dst)
      if dst in stubs:
        self.cache[dst].add(src)

    for type_, ids in batch_requests.iteritems():
      model = getattr(models.all_models, type_)
      instances = model.query.filter(model.id.in_(ids))
      for instance in instances:
        self.instance_cache[Stub(type_, instance.id)] = instance
    return self.cache[obj]

  def relate(self, src, dst):
    if src < dst:
      return (src, dst)
    else:
      return (dst, src)

  def generate_automappings(self, relationship):
    self.auto_mappings = set()
    with self.benchmark("Automapping generate_automappings"):
      # initial relationship is special since it is already created and
      # processing it would abort the loop so we manually enqueue the
      # neighborhood
      src = Stub.from_source(relationship)
      dst = Stub.from_destination(relationship)
      self._step(src, dst)
      self._step(dst, src)
      count = 0
      while len(self.queue) > 0:
        if len(self.auto_mappings) > rules.count_limit:
          break
        count += 1
        src, dst = entry = self.queue.pop()

        if not (self._can_map_to(src, relationship) and
                self._can_map_to(dst, relationship)):
          continue

        created = self._ensure_relationship(src, dst)
        self.processed.add(entry)
        if not created:
          # If the edge already exists it means that auto mappings for it have
          # already been processed and it is safe to cut here.
          continue
        self._step(src, dst)
        self._step(dst, src)

      if len(self.auto_mappings) <= rules.count_limit:
        self._flush(relationship)
      else:
        relationship._json_extras = {
            'automapping_limit_exceeded': True
        }

  def _can_map_to(self, obj, parent_relationship):
    return is_allowed_update(obj.type, obj.id, parent_relationship.context)

  def _flush(self, parent_relationship):
    if len(self.auto_mappings) == 0:
      return
    with self.benchmark("Automapping flush"):
      current_user = get_current_user()
      now = datetime.now()
      # We are doing an INSERT IGNORE INTO here to mitigate a race condition
      # that happens when multiple simultaneous requests create the same
      # automapping. If a relationship object fails our unique constraint
      # it means that the mapping was already created by another request
      # and we can safely ignore it.
      inserter = Relationship.__table__.insert().prefix_with("IGNORE")
      original = self.relate(Stub.from_source(parent_relationship),
                             Stub.from_destination(parent_relationship))
      db.session.execute(inserter.values([{
          "id": None,
          "modified_by_id": current_user.id,
          "created_at": now,
          "updated_at": now,
          "source_id": src.id,
          "source_type": src.type,
          "destination_id": dst.id,
          "destination_type": dst.type,
          "context_id": None,
          "status": None,
          "automapping_id": parent_relationship.id}
          for src, dst in self.auto_mappings
          if (src, dst) != original]))  # (src, dst) is sorted

  def _step(self, src, dst):
    explicit, implicit = rules[src.type, dst.type]
    self._step_explicit(src, dst, explicit)
    self._step_implicit(src, dst, implicit)

  def _step_explicit(self, src, dst, explicit):
    if len(explicit) != 0:
      src_related = (o for o in self.related(src)
                     if o.type in explicit and o != dst)
      for r in src_related:
        entry = self.relate(r, dst)
        if entry not in self.processed:
          self.queue.add(entry)

  def _step_implicit(self, src, dst, implicit):
    if not hasattr(models.all_models, src.type):
      logging.warning('Automapping by attr: cannot find model %s', src.type)
      return
    instance = self.instance_cache.get(src)
    if instance is None:
      model = getattr(models.all_models, src.type)
      instance = model.query.filter(model.id == src.id).first()
      self.instance_cache[src] = instance
    if instance is None:
      logging.warning("Automapping by attr: cannot load model %s: %s",
                      src.type, str(src.id))
      return
    for attr in implicit:
      if hasattr(instance, attr.name):
        values = getattr(instance, attr.name)
        if not isinstance(values, collections.Iterable):
          values = [values]
        for value in values:
          if value is not None:
            entry = self.relate(Stub(value.type, value.id), dst)
            if entry not in self.processed:
              self.queue.add(entry)
          else:
            logging.warning('Automapping by attr: %s is None', attr.name)
      else:
        logging.warning(
            'Automapping by attr: object %s has no attribute %s',
            str(src), str(attr.name)
        )

  def _ensure_relationship(self, src, dst):
    if dst in self.cache.get(src, []):
      return False
    if src in self.cache.get(dst, []):
      return False

    self.auto_mappings.add((src, dst))

    if src in self.cache:
      self.cache[src].add(dst)
    if dst in self.cache:
      self.cache[dst].add(src)

    return True


def handle_relationship_post(source, destination):
  """Handle posting of special relationships.

  This function handles direct relationships that do not have a relationship
  object. A fake object is created with source and destination and auto
  mappings are then generated.

  Args:
    source: Source model of relationship
    destination: Destination model of relationship

  """
  if source is None:
    logging.warning("Automapping request listener: "
                    "no source, no mappings created")
    return
  if destination is None:
    logging.warning("Automapping request listener: "
                    "no destination, no mappings created")
    return
  relationship = Relationship(source_type=source.type,
                              source_id=source.id,
                              destination_type=destination.type,
                              destination_id=destination.id)
  AutomapperGenerator().generate_automappings(relationship)


def register_automapping_listeners():
  """Register event listeners for auto mapper."""
  # pylint: disable=unused-variable

  @Resource.collection_posted.connect_via(Relationship)
  def handle_relationship_collection_post(sender, objects=None, **kwargs):
    """Handle bulk creation of relationships.

    This handler reuses auto mapper cache and is more efficient than handling
    one object at a time.

    Args:
      objects: list of relationship Models.
    """
    automapper = AutomapperGenerator()
    for obj in objects:
      if obj is None:
        logging.warning("Automapping listener: no obj, no mappings created")
        return
      automapper.generate_automappings(obj)

  @Resource.model_posted_after_commit.connect_via(Request)
  @Resource.model_put_after_commit.connect_via(Request)
  def handle_request(sender, obj=None, src=None, service=None):
    handle_relationship_post(obj, obj.audit)

  # TODO REMOVE ON FINAL COMMIT (FEATURE FLAG REMOVAL)
  # pylint: disable=unused-variable
  @Resource.model_posted_after_commit.connect_via(Audit)
  def handle_audit(sender, obj=None, src=None, service=None):
    if not src.get("create-snapshots"):
      if obj is None:
        logging.warning("Automapping audit listener: "
                        "no obj, no mappings created")
        return
      if obj.program is None:
        logging.warning("Automapping audit listener: "
                        "no program, no mappings created")
        return
      rel = Relationship(source_type=obj.type,
                         source_id=obj.id,
                         destination_type=obj.program.type,
                         destination_id=obj.program.id)
      handle_relationship_post(sender, obj=rel)
