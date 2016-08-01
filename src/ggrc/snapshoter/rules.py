# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc.automapper.rules import Attr


class Types(object):

  all = {
      "AccessGroup",
      "Clause",
      "Contract",
      "Control",
      "DataAsset",
      "Facility",
      "Market",
      "Objective",
      "OrgGroup",
      "Policy",
      "Process",
      "Product",
      "Regulation",
      "Section",
      "Standard",
      "System",
      "Vendor",
      "Risk",
      "Threat"
  }

  ignore = {
      "Assessment",
      "Request",
      "Issue",
      "Workflow",
      "Audit",
      "Person"
  }

class RuleSet(object):
  """RuleSet returns a dictionary of rules

  Expected format of rule_list is the following:

  [
    {"master_object_type", ...},
    {"first degree object types"},
    {"second degree object types"}
  ]

  For all master objects of type master_object_type, it will gather all
  related objects from first degree object types (which can be related via
  relationships table or via direct mapping (in which case you should wrap
  the attribute name in Attr) and gather all of first degrees related objects
  of the types listed in the second degree object type.

  Example:
  [
    {"object_type_1", ["object_type_2", ...]},
    {"type_of_related_object_or_attribute", ["second..."]},
    {"type_of_object_to_snapshot_1", ["type_2", ...]}
  ]

  From it, it will build a dictionary of format:
  {
      "parent_type": {
        "fst": {"type_of_related_object_or_attribute_1", ...},
        "snd": {"type_1", "type_2", ...}
      },
      ...
  }

  """

  def __init__(self, rule_list):
    self.rules = dict()

    # TODO just switch to ordinary dict? but will have to duplicate
    # TODO all object types that have the same snapshoting rules...
    for parents, fstdeg, snddeg in rule_list:
      for parent in parents:
        if not parent in self.rules:
          self.rules[parent] = dict()
        self.rules[parent] = {
          "fst": fstdeg,
          "snd": snddeg
        }


rule_list = [
  [
    {"Audit"},
    {Attr("program")},
    Types.all - Types.ignore
  ],
]

rules = RuleSet(rule_list)
