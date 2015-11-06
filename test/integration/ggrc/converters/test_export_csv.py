# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from os.path import abspath, dirname, join
from flask.json import dumps

from ggrc.app import app
from ggrc.converters import get_importables
from ggrc.models.reflection import AttributeInfo
from integration.ggrc import TestCase

THIS_ABS_PATH = abspath(dirname(__file__))
CSV_DIR = join(THIS_ABS_PATH, 'test_csvs/')


class TestExportEmptyTemplate(TestCase):

  def setUp(self):
    self.client.get("/login")
    self.headers = {
        'Content-Type': 'application/json',
        "X-Requested-By": "gGRC",
        "X-export-view": "blocks",
    }

  def test_basic_policy_template(self):
    data = [{"object_name": "Policy", "fields": "all"}]

    response = self.client.post("/_service/export_csv",
                                data=dumps(data), headers=self.headers)
    self.assertEqual(response.status_code, 200)
    self.assertIn("Title*", response.data)
    self.assertIn("Policy", response.data)

  def test_multiple_empty_objects(self):
    data = [
        {"object_name": "Policy", "fields": "all"},
        {"object_name": "Regulation", "fields": "all"},
        {"object_name": "Clause", "fields": "all"},
        {"object_name": "OrgGroup", "fields": "all"},
        {"object_name": "Contract", "fields": "all"},
    ]

    response = self.client.post("/_service/export_csv",
                                data=dumps(data), headers=self.headers)
    self.assertEqual(response.status_code, 200)
    self.assertIn("Title*", response.data)
    self.assertIn("Policy", response.data)
    self.assertIn("Regulation", response.data)
    self.assertIn("Contract", response.data)
    self.assertIn("Clause", response.data)
    self.assertIn("Org Group", response.data)


class TestExportSingleObject(TestCase):

  @classmethod
  def setUpClass(cls):
    TestCase.clear_data()
    cls.tc = app.test_client()
    cls.tc.get("/login")
    cls.import_file("data_for_export_testing.csv")

  @classmethod
  def import_file(cls, filename, dry_run=False):
    data = {"file": (open(join(CSV_DIR, filename)), filename)}
    headers = {
        "X-test-only": "true" if dry_run else "false",
        "X-requested-by": "gGRC",
    }
    cls.tc.post("/_service/import_csv",
                data=data, headers=headers)

  def setUp(self):
    self.client.get("/login")
    self.headers = {
        'Content-Type': 'application/json',
        "X-Requested-By": "gGRC",
        "X-export-view": "blocks",
    }

  def export_csv(self, data):
    return self.client.post("/_service/export_csv", data=dumps(data),
                            headers=self.headers)

  def test_simple_export_query(self):
    data = [{
        "object_name": "Program",
        "filters": {
            "expression": {
                "left": "title",
                "op": {"name": "="},
                "right": "Cat ipsum 1",
            },
        },
        "fields": "all",
    }]
    response = self.export_csv(data)
    expected = set([1])
    for i in range(1, 24):
      if i in expected:
        self.assertIn(",Cat ipsum {},".format(i), response.data)
      else:
        self.assertNotIn(",Cat ipsum {},".format(i), response.data)

    data = [{
        "object_name": "Program",
        "filters": {
            "expression": {
                "left": "title",
                "op": {"name": "~"},
                "right": "1",
            },
        },
        "fields": "all",
    }]
    response = self.export_csv(data)
    expected = set([1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21])
    for i in range(1, 24):
      if i in expected:
        self.assertIn(",Cat ipsum {},".format(i), response.data)
      else:
        self.assertNotIn(",Cat ipsum {},".format(i), response.data)

  def test_boolean_query_parameters(self):
    data = [{
        "object_name": "Program",
        "filters": {
            "expression": {
                "left": "private",
                "op": {"name": "="},
                "right": "1",
            },
        },
        "fields": "all",
    }]
    response = self.export_csv(data)
    expected = set([10, 17, 18, 19, 20, 21, 22])
    for i in range(1, 24):
      if i in expected:
        self.assertIn(",Cat ipsum {},".format(i), response.data)
      else:
        self.assertNotIn(",Cat ipsum {},".format(i), response.data)

  def test_and_export_query(self):
    data = [{
        "object_name": "Program",
        "filters": {
            "expression": {
                "left": {
                    "left": "title",
                    "op": {"name": "!~"},
                    "right": "2",
                },
                "op": {"name": "AND"},
                "right": {
                    "left": "title",
                    "op": {"name": "~"},
                    "right": "1",
                },
            },
        },
        "fields": "all",
    }]
    response = self.export_csv(data)

    expected = set([1, 10, 11, 13, 14, 15, 16, 17, 18, 19])
    for i in range(1, 24):
      if i in expected:
        self.assertIn(",Cat ipsum {},".format(i), response.data)
      else:
        self.assertNotIn(",Cat ipsum {},".format(i), response.data)

  def test_simple_relevant_query(self):
    data = [{
        "object_name": "Program",
        "filters": {
            "expression": {
                "op": {"name": "relevant"},
                "object_name": "Contract",
                "slugs": ["contract-25", "contract-40"],
            },
        },
        "fields": "all",
    }]
    response = self.export_csv(data)

    expected = set([1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 13, 14, 16])
    for i in range(1, 24):
      if i in expected:
        self.assertIn(",Cat ipsum {},".format(i), response.data)
      else:
        self.assertNotIn(",Cat ipsum {},".format(i), response.data)

  def test_program_audit_relevant_query(self):
    data = [{  # should return just program prog-1
        "object_name": "Program",
        "filters": {
            "expression": {
                "op": {"name": "relevant"},
                "object_name": "Audit",
                "slugs": ["au-1"],
            },
        },
        "fields": "all",
    }, {  # Audits : au-1, au-3, au-5, au-7,
        "object_name": "Audit",
        "filters": {
            "expression": {
                "op": {"name": "relevant"},
                "object_name": "__previous__",
                "ids": ["0"],
            },
        },
        "fields": "all",
    }]
    response = self.export_csv(data)

    self.assertIn(",Cat ipsum 1,", response.data)
    expected = set([1, 3, 5, 7])
    for i in range(1, 14):
      if i in expected:
        self.assertIn(",Audit {},".format(i), response.data)
      else:
        self.assertNotIn(",Audit {},".format(i), response.data)

  def test_section_policy_relevant_query(self):
    data = [{  # sec-1
        "object_name": "Section",
        "filters": {
            "expression": {
                "op": {"name": "relevant"},
                "object_name": "Policy",
                "slugs": ["p1"],
            },
        },
        "fields": "all",
    }, {  # p3
        "object_name": "Policy",
        "filters": {
            "expression": {
                "op": {"name": "relevant"},
                "object_name": "Section",
                "slugs": ["sec-3"],
            },
        },
        "fields": "all",
    }, {  # sec-8
        "object_name": "Section",
        "filters": {
            "expression": {
                "op": {"name": "relevant"},
                "object_name": "Standard",
                "slugs": ["std-1"],
            },
        },
        "fields": "all",
    }, {  # std-3
        "object_name": "Standard",
        "filters": {
            "expression": {
                "op": {"name": "relevant"},
                "object_name": "Section",
                "slugs": ["sec-10"],
            },
        },
        "fields": "all",
    }, {  # sec-5
        "object_name": "Section",
        "filters": {
            "expression": {
                "op": {"name": "relevant"},
                "object_name": "Regulation",
                "slugs": ["reg-2"],
            },
        },
        "fields": "all",
    }, {  # reg-1
        "object_name": "Regulation",
        "filters": {
            "expression": {
                "op": {"name": "relevant"},
                "object_name": "Section",
                "slugs": ["sec-4"],
            },
        },
        "fields": "all",
    }]
    response = self.export_csv(data)

    titles = [",mapped section {},".format(i) for i in range(1, 11)]
    titles.extend([",mapped reg {},".format(i) for i in range(1, 11)])
    titles.extend([",mapped policy {},".format(i) for i in range(1, 11)])
    titles.extend([",mapped standard {},".format(i) for i in range(1, 11)])

    expected = set([
        ",mapped section 1,",
        ",mapped section 5,",
        ",mapped section 8,",
        ",mapped reg 1,",
        ",mapped standard 3,",
        ",mapped policy 3,",
    ])

    for title in titles:
      if title in expected:
        self.assertIn(title, response.data, "'{}' not found".format(title))
      else:
        self.assertNotIn(title, response.data, "'{}' was found".format(title))

  def test_multiple_relevant_query(self):
    data = [{
        "object_name": "Program",
        "filters": {
            "expression": {
                "left": {
                    "op": {"name": "relevant"},
                    "object_name": "Policy",
                    "slugs": ["policy-3"],
                },
                "op": {"name": "AND"},
                "right": {
                    "op": {"name": "relevant"},
                    "object_name": "Contract",
                    "slugs": ["contract-25", "contract-40"],
                },
            },
        },
        "fields": "all",
    }]
    response = self.export_csv(data)

    expected = set([1, 2, 4, 8, 10, 11, 13])
    for i in range(1, 24):
      if i in expected:
        self.assertIn(",Cat ipsum {},".format(i), response.data)
      else:
        self.assertNotIn(",Cat ipsum {},".format(i), response.data)

  def test_query_all_aliases(self):
    def rhs(model, attr):
      attr = getattr(model, attr, None)
      if attr is not None and hasattr(attr, "_query_clause_element"):
        class_name = attr._query_clause_element().type.__class__.__name__
        if class_name == "Boolean":
          return "1"
      return "1/1/2015"

    data = lambda model, attr, field: [{
        "object_name": model.__name__,
        "fields": "all",
        "filters": {
            "expression": {
                "left": field.lower(),
                "op": {"name": "="},
                "right": rhs(model, attr)
            },
        }
    }]

    failed = set()
    for model in set(get_importables().values()):
      for attr, field in AttributeInfo(model)._aliases.items():
        if field is None:
          continue
        try:
         field = field["display_name"] if type(field) is dict else field
         res = self.export_csv(data(model, attr, field))
         self.assertEqual(res.status_code, 200)
        except Exception as e:
          failed.add((model, attr, field, e))
    self.assertEqual(sorted(failed), [])


class TestExportMultipleObjects(TestCase):

  @classmethod
  def setUpClass(cls):
    TestCase.clear_data()
    cls.tc = app.test_client()
    cls.tc.get("/login")
    cls.import_file("data_for_export_testing.csv")

  @classmethod
  def import_file(cls, filename, dry_run=False):
    data = {"file": (open(join(CSV_DIR, filename)), filename)}
    headers = {
        "X-test-only": "true" if dry_run else "false",
        "X-requested-by": "gGRC",
    }
    cls.tc.post("/_service/import_csv",
                data=data, headers=headers)

  def setUp(self):
    self.client.get("/login")
    self.headers = {
        'Content-Type': 'application/json',
        "X-Requested-By": "gGRC",
        "X-export-view": "blocks",
    }

  def export_csv(self, data):
    return self.client.post("/_service/export_csv", data=dumps(data),
                            headers=self.headers)

  def test_simple_multi_export(self):
    data = [{
        "object_name": "Program",  # prog-1
        "filters": {
            "expression": {
                "left": "title",
                "op": {"name": "="},
                "right": "cat ipsum 1"
            },
        },
        "fields": "all",
    }, {
        "object_name": "Regulation",  # regulation-9000
        "filters": {
            "expression": {
                "left": "title",
                "op": {"name": "="},
                "right": "Hipster ipsum A 1"
            },
        },
        "fields": "all",
    }]
    response = self.export_csv(data)

    self.assertIn(",Cat ipsum 1,", response.data)
    self.assertIn(",Hipster ipsum A 1,", response.data)

  def test_relevant_to_previous_export(self):
    data = [{
        "object_name": "Program",  # prog-1, prog-23
        "filters": {
            "expression": {
                "left": {
                    "left": "title",
                    "op": {"name": "="},
                    "right": "cat ipsum 1"
                },
                "op": {"name": "OR"},
                "right": {
                    "left": "title",
                    "op": {"name": "="},
                    "right": "cat ipsum 23"
                },
            },
        },
        "fields": ["slug", "title", "description"],
    }, {
        "object_name": "Contract",  # contract-25, contract-27, contract-47
        "filters": {
            "expression": {
                "op": {"name": "relevant"},
                "object_name": "__previous__",
                "ids": ["0"],
            },
        },
        "fields": ["slug", "title", "description"],
    }, {
        "object_name": "Control",  # control-3, control-4, control-5
        "filters": {
            "expression": {
                "left": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["0"],
                },
                "op": {"name": "AND"},
                "right": {
                    "left": {
                        "left": "code",
                        "op": {"name": "!~"},
                        "right": "1"
                    },
                    "op": {"name": "AND"},
                    "right": {
                        "left": "code",
                        "op": {"name": "!~"},
                        "right": "2"
                    },
                },
            },
        },
        "fields": ["slug", "title", "description"],
    }, {
        "object_name": "Policy",  # policy - 3, 4, 5, 6, 15, 16
        "filters": {
            "expression": {
                "left": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["0"],
                },
                "op": {"name": "AND"},
                "right": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["2"],
                },
            },
        },
        "fields": ["slug", "title", "description"],
    }
    ]
    response = self.export_csv(data)

    # programs
    for i in range(1, 24):
      if i in (1, 23):
        self.assertIn(",Cat ipsum {},".format(i), response.data)
      else:
        self.assertNotIn(",Cat ipsum {},".format(i), response.data)

    # contracts
    for i in range(5, 121, 5):
      if i in (5, 15, 115):
        self.assertIn(",con {},".format(i), response.data)
      else:
        self.assertNotIn(",con {},".format(i), response.data)

    # controls
    for i in range(115, 140):
      if i in (117, 118, 119) + (121, 122):
        self.assertIn(",Startupsum {},".format(i), response.data)
      else:
        self.assertNotIn(",Startupsum {},".format(i), response.data)

    # policies
    for i in range(5, 25):
      if i in (7, 8, 9, 10, 19, 20) + (11, 12, 13, 14, 15, 16, 17, 18, 19):
        self.assertIn(",Cheese ipsum ch {},".format(i), response.data)
      else:
        self.assertNotIn(",Cheese ipsum ch {},".format(i), response.data)
