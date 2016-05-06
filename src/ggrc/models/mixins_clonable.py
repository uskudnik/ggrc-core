# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

"""A mixin for objects that can be cloned"""

from ggrc.services import common


class Clonable(object):
  """Clonable mixin"""

  __lazy_init__ = True

  CLONEABLE_CHILDREN = {}

  _operation_data = {}

  @classmethod
  def init(cls, model):
    cls.set_handlers(model)

  @classmethod
  def set_handlers(cls, model):
    @common.Resource.model_put_after_commit.connect_via(model)
    def handle_model_clone(sender, obj=None, src=None, service=None):
      # pylint: disable=unused-argument, unused-variable
      if src.get("operation", "") == u"clone":
        obj.clone(children=src.get("associatedObjects", []))

  def generate_attribute(self, attribute):
    """Generate a new unique attribute as a copy of original"""
    attr = getattr(self, attribute)

    def count_values(key, value):
      return self.query.filter_by(**{key: value}).count()

    i = 1
    generated_attr_value = "{0} - copy {1}".format(attr, i)
    while count_values(attribute, generated_attr_value):
      i += 1
      generated_attr_value = "{0} - copy {1}".format(attr, i)
    return generated_attr_value

  def clone_custom_attribute_values(self, obj):
    """Copy object's custom attribute values"""
    ca_values = self.custom_attribute_values

    for value in ca_values:
      value._clone(obj)  # pylint: disable=protected-access
