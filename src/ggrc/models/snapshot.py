# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for Snapshot object"""

from datetime import datetime

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import orm
from sqlalchemy import event
from sqlalchemy import inspect
from sqlalchemy.orm.session import Session
from sqlalchemy import func
from sqlalchemy.sql.expression import tuple_

from ggrc import db
from ggrc.utils import benchmark
from ggrc.login import get_current_user_id
from ggrc.models import mixins
from ggrc.models import reflection
from ggrc.models import relationship
from ggrc.models import revision
from ggrc.models.deferred import deferred
from ggrc.models.computed_property import computed_property


class Snapshot(relationship.Relatable, mixins.Base, db.Model):
  """Snapshot object that holds a join of parent object, revision, child object
  and parent object's context.

  Conceptual model is that we have a parent snapshotable object (e.g. Audit)
  which will not create relationships to objects with automapper at the time of
  creation but will instead create snapshots of those objects based on the
  latest revision of the object at the time of create / update of the object.
  Objects that were supposed to be mapped are called child objects.
  """
  __tablename__ = "snapshots"

  _publish_attrs = [
      "parent",
      "child_id",
      "child_type",
      "revision",
      "revision_id",
      reflection.PublishOnly("revisions"),
      reflection.PublishOnly("is_latest_revision"),
  ]

  _update_attrs = [
      "parent",
      "child_id",
      "child_type",
      "update_revision"
  ]

  _include_links = [
      "revision"
  ]

  parent_id = deferred(db.Column(db.Integer, nullable=False), "Snapshot")
  parent_type = deferred(db.Column(db.String, nullable=False), "Snapshot")

  # Child ID and child type are data denormalisations - we could easily get
  # them from revision.content, but since that is a JSON field it will be
  # easier for development to just denormalise on write and not worry
  # about it.
  child_id = deferred(db.Column(db.Integer, nullable=False), "Snapshot")
  child_type = deferred(db.Column(db.String, nullable=False), "Snapshot")

  revision_id = deferred(db.Column(
      db.Integer,
      db.ForeignKey("revisions.id"),
      nullable=False
  ), "Snapshot")
  revision = db.relationship(
      "Revision",
  )
  _update_revision = None

  revisions = db.relationship(
      "Revision",
      primaryjoin="and_(Revision.resource_id == foreign(Snapshot.child_id),"
      "Revision.resource_type == foreign(Snapshot.child_type))",
      uselist=True,
  )

  @computed_property
  def is_latest_revision(self):
    """Flag if the snapshot has the latest revision."""
    return self.revisions and self.revision == self.revisions[-1]

  @classmethod
  def eager_query(cls):
    query = super(Snapshot, cls).eager_query()
    return cls.eager_inclusions(query, Snapshot._include_links).options(
        orm.subqueryload('revision'),
        orm.subqueryload('revisions'),
    )

  @hybrid_property
  def update_revision(self):
    return self.revision_id

  @update_revision.setter
  def update_revision(self, value):
    self._update_revision = value
    if value == "latest":
      _set_latest_revisions([self])

  @property
  def parent_attr(self):
    return '{0}_parent'.format(self.parent_type)

  @property
  def parent(self):
    return getattr(self, self.parent_attr)

  @parent.setter
  def parent(self, value):
    self.parent_id = getattr(value, 'id', None)
    self.parent_type = getattr(value, 'type', None)
    return setattr(self, self.parent_attr, value)

  @staticmethod
  def _extra_table_args(_):
    return (
        db.UniqueConstraint(
            "parent_type", "parent_id",
            "child_type", "child_id"),
        db.Index("ix_snapshots_parent", "parent_type", "parent_id"),
        db.Index("ix_snapshots_child", "child_type", "child_id"),
    )


def handle_post_flush(session, flush_context, instances):
  """Handle snapshot objects on api post requests."""
  # pylint: disable=unused-argument
  # Arguments here are set in the event listener and are mandatory.

  with benchmark("Snapshot pre flush handler"):

    snapshots = [o for o in session if isinstance(o, Snapshot)]
    if not snapshots:
      return

    with benchmark("Snapshot revert attrs"):
      _revert_attrs(snapshots)

    new_snapshots = [o for o in snapshots
                     if getattr(o, "_update_revision", "") == "new"]
    if new_snapshots:
      with benchmark("Snapshot post api set revisions"):
        _set_latest_revisions(new_snapshots)
      with benchmark("Snapshot post api ensure relationships"):
        _ensure_program_relationships(new_snapshots)


def _revert_attrs(objects):
  """Revert any modified attributes on snapshot.

  All snapshot attributes that are updatable with API calls should only be
  settable and not editable. This function reverts any possible edits to
  existing values.
  """
  attrs = ["parent_id", "parent_type", "child_id", "child_type"]
  for snapshot in objects:
    for attr in attrs:
      deleted = inspect(snapshot).attrs[attr].history.deleted
      if deleted:
        setattr(snapshot, attr, deleted[0])


def _ensure_program_relationships(objects):
  """Ensure that snapshotted object is related to audit program.

  This function is made to handle multiple snapshots for a single audit.
  Args:
    objects: list of snapshot objects with child_id and child_type set.
  """
  pairs = [(o.child_type, o.child_id) for o in objects]
  assert len({o.parent.id for o in objects}) == 1  # fail on multiple audits
  program = ("Program", objects[0].parent.program_id)
  rel = relationship.Relationship
  columns = db.session.query(
      rel.destination_type,
      rel.destination_id,
      rel.source_type,
      rel.source_id,
  )
  query = columns.filter(
      tuple_(rel.destination_type, rel.destination_id) == (program),
      tuple_(rel.source_type, rel.source_id).in_(pairs)
  ).union(
      columns.filter(
          tuple_(rel.source_type, rel.source_id) == (program),
          tuple_(rel.destination_type, rel.destination_id).in_(pairs)
      )
  )
  existing_pairs = set(sum([
      [(r.destination_type, r.destination_id), (r.source_type, r.source_id)]
      for r in query
  ], []))  # build a set of all found type-id pairs
  missing_pairs = set(pairs).difference(existing_pairs)
  _insert_program_relationships(program, missing_pairs)


def _insert_program_relationships(program, missing_pairs):
  """Insert missing obj-program relationships."""
  if not missing_pairs:
    return
  current_user_id = get_current_user_id()
  now = datetime.now()
  # We are doing an INSERT IGNORE INTO here to mitigate a race condition
  # that happens when multiple simultaneous requests create the same
  # automapping. If a relationship object fails our unique constraint
  # it means that the mapping was already created by another request
  # and we can safely ignore it.
  inserter = relationship.Relationship.__table__.insert().prefix_with(
      "IGNORE")
  db.session.execute(
      inserter.values([
          {
              "id": None,
              "modified_by_id": current_user_id,
              "created_at": now,
              "updated_at": now,
              "source_type": program[0],
              "source_id": program[1],
              "destination_type": dst_type,
              "destination_id": dst_id,
              "context_id": None,
              "status": None,
              "automapping_id": None
          }
          for dst_type, dst_id in missing_pairs
      ])
  )


def _set_latest_revisions(objects):
  """Set latest revision_id for given child_type.

  Args:
    objects: list of snapshot objects with child_id and child_type set.
  """
  pairs = [(o.child_type, o.child_id) for o in objects]
  query = db.session.query(
      func.max(revision.Revision.id, name="id", identifier="id"),
      revision.Revision.resource_type,
      revision.Revision.resource_id,
  ).filter(
      tuple_(
          revision.Revision.resource_type,
          revision.Revision.resource_id,
      ).in_(pairs)
  ).group_by(
      revision.Revision.resource_type,
      revision.Revision.resource_id,
  )
  id_map = {(r_type, r_id): id_ for id_, r_type, r_id in query}
  for o in objects:
    o.revision_id = id_map.get((o.child_type, o.child_id))


event.listen(Session, 'before_flush', handle_post_flush)
