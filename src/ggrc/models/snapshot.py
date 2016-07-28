# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for Snapshot object"""

from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models import mixins


class Snapshot(mixins.Base, db.Model):
  """Snapshot object that holds a join of parent object, revision, child object
  and parent object's context.

  Conceptual model is that we have a parent snapshotable object (e.g. Audit)
  which will not create relationships to objects with automapper at the time of
  creation but will instead create snapshots of those objects based on the
  latest revision of the object at the time of create / update of the object.
  Objects that were supposed to be mapped are called child objects.
  """
  __tablename__ = "snapshots"

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
      db.ForeignKey("revisions.id")
  ), "Snapshot")
  revision = db.relationship(
      "Revision",
  )

  _publish_attrs = [
      "parent",
      "child_id",
      "child_type",
      "revision",
      "revision_id",
  ]

  @classmethod
  def eager_query(cls):
    query = super(Snapshot, cls).eager_query()
    return query.options(
        orm.subqueryload('revision'),
    )

  @staticmethod
  def _extra_table_args(_):
    return (
        db.UniqueConstraint(
            "parent_type", "parent_id",
            "child_type", "child_id"),
        db.Index("ix_snapshots_parent", "parent_type", "parent_id"),
        db.Index("ix_snapshots_child", "child_type", "child_id"),
    )

  _publish_attrs = [
      "parent",
      "child_id",
      "child_type",
      "revision",
      "revision_id",
  ]
