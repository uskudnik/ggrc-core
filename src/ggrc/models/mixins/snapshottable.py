# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for Snapshot object"""

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import orm


from ggrc import db
from ggrc.models.snapshot import Snapshot


class SnapshottableParent(object):
  """Provide `snapshotted_objects` on for parent objects."""

  _publish_attrs = [
      "snapshotted_objects",
  ]

  @declared_attr
  def snapshotted_objects(cls):  # pylint: disable=no-self-argument
    """Return all snapshotted objects"""
    return db.relationship(
        Snapshot,
        primaryjoin=lambda: and_(
            orm.remote(ggrc.models.Snapshot.parent_id) == cls.id,
            orm.remote(ggrc.models.Snapshot.parent_type) == cls.__name__
        ),
        foreign_keys='Snapshot.parent_id,Snapshot.parent_type,',
        backref='{0}_parent'.format(cls.__name__),
        cascade='all, delete-orphan')

  @classmethod
  def eager_query(cls):
    query = super(SnapshottableParent, cls).eager_query()
    return query.options(
        orm.subqueryload("snapshotted_objects").undefer_group(
            "Snapshot_complete"
        ),
    )
