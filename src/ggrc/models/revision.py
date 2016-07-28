# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Defines a Revision model for storing snapshots."""

from ggrc import db
from ggrc.models.computed_property import computed_property
from ggrc.models.mixins import Base
from ggrc.models.types import JsonType


class Revision(Base, db.Model):
  """Revision object holds a JSON snapshot of the object at a time."""

  __tablename__ = 'revisions'

  resource_id = db.Column(db.Integer, nullable=False)
  resource_type = db.Column(db.String, nullable=False)
  event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
  action = db.Column(db.Enum(u'created', u'modified', u'deleted'),
                     nullable=False)
  content = db.Column(JsonType, nullable=False)

  source_type = db.Column(db.String, nullable=True)
  source_id = db.Column(db.Integer, nullable=True)
  destination_type = db.Column(db.String, nullable=True)
  destination_id = db.Column(db.Integer, nullable=True)

  snapshots = db.relationship("Snapshot")

  @staticmethod
  def _extra_table_args(_):
    return (
        db.Index("revisions_modified_by", "modified_by_id"),
        db.Index("fk_revisions_resource", "resource_type", "resource_id"),
        db.Index("fk_revisions_source", "source_type", "source_id"),
        db.Index("fk_revisions_destination",
                 "destination_type", "destination_id"),
    )

  _publish_attrs = [
      'resource_id',
      'resource_type',
      'source_type',
      'source_id',
      'destination_type',
      'destination_id',
      'action',
      'content',
      'description',
  ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Revision, cls).eager_query()
    return query.options(
        orm.subqueryload('modified_by'),
        orm.subqueryload('event'),  # used in description
    )

  def __init__(self, obj, modified_by_id, action, content):
    self.resource_id = obj.id
    self.modified_by_id = modified_by_id
    self.resource_type = str(obj.__class__.__name__)
    self.action = action
    self.content = content

    for attr in ["source_type",
                 "source_id",
                 "destination_type",
                 "destination_id"]:
      setattr(self, attr, getattr(obj, attr, None))

  def _description_mapping(self, link_objects):
    """Compute description for revisions with <-> in display name."""
    display_name = self.content['display_name']
    source, destination = display_name.split('<->')[:2]
    mapping_verb = "linked" if self.resource_type in link_objects else "mapped"
    if self.action == 'created':
      result = u"{1} {2} to {0}".format(source, destination, mapping_verb)
    elif self.action == 'deleted':
      result = u"{1} un{2} from {0}".format(source, destination, mapping_verb)
    else:
      result = u"{0} {1}".format(display_name, self.action)
    return result

  @computed_property
  def description(self):
    """Compute a human readable description from action and content."""
    link_objects = ['ObjectDocument']
    if 'display_name' not in self.content:
      return ''
    display_name = self.content['display_name']
    if not display_name:
      result = u"{0} {1}".format(self.resource_type, self.action)
    elif u'<->' in display_name:
      result = self._description_mapping(link_objects)
    else:
      if 'mapped_directive' in self.content:
        # then this is a special case of combined map/creation
        # should happen only for Section and Control
        mapped_directive = self.content['mapped_directive']
        if self.action == 'created':
          result = u"New {0}, {1}, created and mapped to {2}".format(
              self.resource_type,
              display_name,
              mapped_directive
          )
        elif self.action == 'deleted':
          result = u"{0} unmapped from {1} and deleted".format(
              display_name, mapped_directive)
        else:
          result = u"{0} {1}".format(display_name, self.action)
      else:
        # otherwise, it's a normal creation event
        result = u"{0} {1}".format(display_name, self.action)
    if self.event.action == "BULK":
      result += ", via bulk action"
    return result
