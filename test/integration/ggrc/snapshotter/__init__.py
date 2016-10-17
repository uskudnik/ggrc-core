# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Base test case for testing snapshotter"""

from os.path import abspath, dirname, join

import ggrc.models as models


import integration.ggrc
from integration.ggrc import api_helper
from integration.ggrc.converters import TestCase
import integration.ggrc.generator


THIS_ABS_PATH = abspath(dirname(__file__))
CSV_DIR = join(THIS_ABS_PATH, "../converters/test_csvs/")


def snapshot_identity(s_1, s_2):
  return (s_1.id == s_2.id and
          s_1.updated_at == s_2.updated_at and
          s_1.child_id == s_2.child_id and
          s_1.child_type == s_2.child_type and
          s_1.revision_id == s_2.revision_id)


class SnapshotterBaseTestCase(TestCase):
  """Test cases for Snapshoter module"""

  # pylint: disable=invalid-name

  def setUp(self):
    integration.ggrc.TestCase.setUp(self)
    self.objgen = integration.ggrc.generator.ObjectGenerator()
    self.api = api_helper.Api()

  def tearDown(self):
    integration.ggrc.TestCase.tearDown(self)

  def create_object(self, cls, data):
    _, obj = self.objgen.generate_object(cls, data)
    return obj

  def create_mapping(self, src, dst):
    _, obj = self.objgen.generate_relationship(src, dst)
    return obj

  def create_audit(self, program):
    self.create_object(models.Audit, {
        "title": "Snapshotable audit",
        "program": {"id": program.id},
        "status": "Planned",
        "snapshots": {
            "operation": "create",
        }
    })

  @classmethod
  def refresh_object(cls, obj):
    """Returns a new instance of a model, fresh and warm from the database."""
    return obj.query.filter_by(id=obj.id).one()
