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

  @classmethod
  def from_dict(cls, _dict):
    return Stub(_dict["type"], _dict["id"])


class Family(collections.namedtuple("Family", ["parent", "children"])):

  def __contains__(self, item):
    pass


Operation = collections.namedtuple(
    "Operation", ["type", "success", "response"])
OperationResponse = collections.namedtuple(
    "OperationResponse", ["success", "response"])
