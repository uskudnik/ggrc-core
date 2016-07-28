# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for Snapshot object"""

from ggrc import db
from ggrc.models import mixins


class Snapshot(mixins.Base, db.Model):
  """Snapshot object that holds a join of object, revision and context"""
  __tablename__ = "snapshots"

  parent_id = db.Column(db.Integer, nullable=False)
  parent_type = db.Column(db.String, nullable=False)

  child_id = db.Column(db.Integer, nullable=False)
  child_type = db.Column(db.String, nullable=False)

  revision_id = db.Column(
      db.Integer,
      db.ForeignKey("revisions.id")
  )
  revision = db.relationship(
      "Revision",
      back_populates="snapshots",
      lazy="joined"  # eager load the revisions
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
