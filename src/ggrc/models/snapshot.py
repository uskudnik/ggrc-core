# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for Snapshot object"""

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import orm
from sqlalchemy import and_
from sqlalchemy import or_

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
      db.ForeignKey("revisions.id"),
      primary_key=True
  )
  revision = db.relationship(
      "Revision",
      back_populates="snapshots",
      lazy="joined"  # eager load the revisions
  )

  @property
  def parent_attr(self):
    return '{0}_parent'.format(self.parent_type)

  @property
  def parent(self):
    return getattr(self, self.parent_attr)

  @parent.setter
  def parent(self, value):
    self.parent_id = value.id if value is not None else None
    self.parent_type = value.__class__.__name__ if value is not None else None
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

  _publish_attrs = [
    "parent",
    "child_id",
    "child_type",
    "revision",
    "revision_id",
  ]

class Snapshotable(object):
  @declared_attr
  def snapshoted_objects(cls):
    print "snapshoted_objects", cls.__name__
    joinstr = "and_(remote(Snapshot.parent_id) == {type}.id, " \
              "remote(Snapshot.parent_type) == '{type}')".format(
      type=cls.__name__)
    return db.relationship(
      lambda: Snapshot,
      primaryjoin=joinstr,
      foreign_keys='Snapshot.parent_id,Snapshot.parent_type,',
      backref='{0}_parent'.format(cls.__name__),
      cascade='all, delete-orphan')

  _publish_attrs = [
    "snapshoted_objects"
  ]

  @classmethod
  def eager_query(cls):
    query = super(Snapshotable, cls).eager_query()
    return cls.eager_inclusions(query, Snapshotable._publish_attrs).options(
      orm.subqueryload('snapshoted_objects'),
    )
