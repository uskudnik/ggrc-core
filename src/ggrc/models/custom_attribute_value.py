# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: laran@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

"""Custom attribute value model"""

from sqlalchemy import or_

from ggrc import db
from ggrc.models.mixins import Base


class CustomAttributeValue(Base, db.Model):
  """Custom attribute value model"""

  __tablename__ = 'custom_attribute_values'

  custom_attribute_id = db.Column(
      db.Integer,
      db.ForeignKey('custom_attribute_definitions.id', ondelete="CASCADE")
  )
  attributable_id = db.Column(db.Integer)
  attributable_type = db.Column(db.String)
  attribute_value = db.Column(db.String)

  # When the attibute is of a mapping type this will hold the id of the mapped
  # object while attribute_value will hold the type name.
  # For example an instance of attribute type Map:Person will have a person id
  # in attribute_object_id and string 'Person' in attribute_value.
  attribute_object_id = db.Column(db.Integer)

  @property
  def attributable_attr(self):
    return '{0}_attributable'.format(self.attributable_type)

  @property
  def attributable(self):
    return getattr(self, self.attributable_attr)

  @attributable.setter
  def attributable(self, value):
    self.attributable_id = value.id if value is not None else None
    self.attributable_type = value.__class__.__name__ if value is not None \
        else None
    return setattr(self, self.attributable_attr, value)

  _publish_attrs = [
      'custom_attribute_id',
      'attributable_id',
      'attributable_type',
      'attribute_value',
      'attribute_object',
  ]

  @property
  def attribute_object(self):
    """Fetch the object referred to by attribute_object_id.

    Use backrefs defined in CustomAttributeMapable.

    Returns:
        A model instance of type specified in attribute_value
    """
    return getattr(self, self._attribute_object_attr)

  @attribute_object.setter
  def attribute_object(self, value):
    """Set attribute_object_id via whole object.

    Args:
        value: model instance
    """
    self.attribute_object_id = value.id
    return setattr(self, self._attribute_object_attr, value)

  @property
  def attribute_object_type(self):
    """Fetch the mapped object pointed to by attribute_object_id.

    Returns:
       A model of type referenced in attribute_value
    """
    attr_type = self.custom_attribute.attribute_type
    if not attr_type.startswith("Map:"):
      return None
    return self.attribute_object.__class__.__name__

  @property
  def _attribute_object_attr(self):
    """Compute the relationship property based on object type.

    Returns:
        Property name
    """
    attr_type = self.custom_attribute.attribute_type
    if not attr_type.startswith("Map:"):
      return None
    return 'attribute_{0}'.format(self.attribute_value)

  @classmethod
  def mk_filter_by_custom(cls, obj_class, custom_attribute_id):
    from ggrc.models import all_models
    attr_def = all_models.CustomAttributeDefinition.query.filter_by(
        id=custom_attribute_id
    ).first()
    if attr_def.attribute_type.startswith("Map:"):
      map_type = attr_def.attribute_type[4:]
      map_class = getattr(all_models, map_type, None)
      if map_class:
        fields = [getattr(map_class, name, None)
                  for name in ["email", "title", "slug"]]
        fields = [field for field in fields if field is not None]

        def filter_by(predicate):
          return cls.query.filter(
              (cls.custom_attribute_id == custom_attribute_id) &
              (cls.attributable_type == obj_class.__name__) &
              (cls.attributable_id == obj_class.id) &
              (map_class.query.filter(
                  (map_class.id == cls.attribute_object_id) &
                  or_(*[predicate(f) for f in fields])).exists())
          ).exists()
        return filter_by

    def filter_by(predicate):
      return cls.query.filter(
          (cls.custom_attribute_id == custom_attribute_id) &
          (cls.attributable_type == obj_class.__name__) &
          (cls.attributable_id == obj_class.id) &
          predicate(cls.attribute_value)
      ).exists()
    return filter_by

  def _clone(self, obj):
    """Clone a custom value to a new object."""
    data = {
        "custom_attribute_id": self.custom_attribute_id,
        "attributable_id": obj.id,
        "attributable_type": self.attributable_type,
        "attribute_value": self.attribute_value,
        "attribute_object_id": self.attribute_object_id
    }
    ca_value = CustomAttributeValue(**data)
    db.session.add(ca_value)
    db.session.flush()
    return ca_value
