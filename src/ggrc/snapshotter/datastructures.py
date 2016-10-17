# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Various data structures used for snapshot generator"""

import collections


Attr = collections.namedtuple('Attr', ['name'])


class Stub(collections.namedtuple("Stub", ["type", "id"])):
  """Simple object representation"""

  @classmethod
  def from_object(cls, _object):
    return Stub(_object.type, _object.id)

  def to_json_stub(self):
    from ggrc.models import all_models
    return {
        "id": self.id,
        "href": "/api/{}/{}".format(
            getattr(all_models, self.type)._inflector.table_name,  # noqa # pylint: disable=protected-access
            self.id),
        "type": self.type,
    }

  @classmethod
  def from_dict(cls, _dict):
    return Stub(_dict["type"], _dict["id"])

  @classmethod
  def from_tuple(cls, _tuple, type_position=0, id_position=1):
    return Stub(_tuple[type_position], _tuple[id_position])


class Pair(collections.namedtuple("Pair", ["parent", "child"])):
  """Simple representation of snapshot object"""

  @classmethod
  def from_4tuple(cls, _tuple,
                  parent_type=0, parent_id=1, child_type=2, child_id=3):
    return Pair(Stub(_tuple[parent_type], _tuple[parent_id]),
                Stub(_tuple[child_type], _tuple[child_id]))

  def to_4tuple(self):
    return self.parent.type, self.parent.id, self.child.type, self.child.id

  @classmethod
  def from_2tuple(cls, _tuple):
    parent, child = _tuple
    return Pair(parent, child)

  def to_2tuple(self):
    return self.parent, self.child


OperationResponse = collections.namedtuple(
    "OperationResponse", ["type", "success", "response", "data"])
