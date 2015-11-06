# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from ggrc.utils import merge_dicts
from ggrc.utils import merge_dict
from ggrc.utils import get_mapping_rules
from unittest import TestCase


class TestUtilsFunctions(TestCase):

  def test_mapping_rules(self):
    """ Test that all mappings go both ways """
    mappings = get_mapping_rules()
    verificationErrors = []

    # Special cases in mappings as defined in utils.py:
    audit_mappings = ["Control", "DataAsset", "Facility", "Market", "OrgGroup",
                      "Process", "Product", "Program", "Project", "System",
                      "Vendor", "AccessGroup", "Request"]

    for object_name, object_mappings in mappings.items():
      for mapping in object_mappings:
        try:
          if mapping == "Request":
            # objects mapped to requests show up as mapped to Audit so
            # Requests are no listed anywhere in the allowed mappings.
            self.assertNotIn(mapping, mappings)
          elif mapping == "Audit" and object_name in audit_mappings:
            self.assertNotIn(
                object_name, mappings[mapping],
                "{} found in {} mappings".format(object_name, mapping)
            )
          else:
            self.assertIn(
                mapping, mappings,
                "- {} is not in the mappings dict".format(mapping)
            )
            self.assertIn(
                object_name, mappings[mapping],
                "{} not found in {} mappings".format(object_name, mapping)
            )
        except AssertionError as e:
          verificationErrors.append(str(e))

    verificationErrors.sort()
    self.assertEqual(verificationErrors, [])

  def test_merge_dict(self):
    dict1 = {
        "a": {
            "b": {
                "c": 1,
                "d": {
                    "e": 2,
                },
            },
        },
    }
    dict2 = {
        "a": {
            "b": {
                "c": 1,
                "f": {
                    "e": 2
                }
            },
            "g": 3
        },
        "h": 4
    }
    expected_result = {
        "a": {
            "b": {
                "c": 1,
                "d": {
                    "e": 2,
                },
                "f": {
                    "e": 2,
                },
            },
            "g": 3,
        },
        "h": 4,
    }

    result = merge_dict(dict1, dict2)

    self.assertEquals(result, expected_result)

  def test_merge_dicts(self):
    dict1 = {
        "a": {
            "b": {
                "c": 1,
                "d": {
                    "e": 2
                }
            }
        }
    }
    dict2 = {
        "a": {
            "b": {
                "c": 1,
                "f": {
                    "e": 2
                }
            },
            "g": 3
        },
        "h": 4
    }
    dict3 = {
        "a": {
            "eeb": {
                "c": 1,
                "f": {
                    "e": 2
                }
            },
            "g": 3
        },
        "h": 4
    }

    result = {
        "a": {
            "b": {
                "c": 1,
                "d": {
                    "e": 2,
                },
                "f": {
                    "e": 2,
                },
            },
            "eeb": {
                "c": 1,
                "f": {
                    "e": 2
                }
            },
            "g": 3,
        },
        "h": 4,
    }
    expected_result = merge_dicts(dict1, dict2, dict3)
    self.assertEqual(result, expected_result)
