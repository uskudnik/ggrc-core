# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc import db
import ggrc.models as models
import integration.ggrc
from integration.ggrc import api_helper
import integration.ggrc.generator


class TestSnapshoting(integration.ggrc.TestCase):
  def setUp(self):
    integration.ggrc.TestCase.setUp(self)
    self.objgen = integration.ggrc.generator.ObjectGenerator()
    self.api = api_helper.Api()

  def tearDown(self):
    integration.ggrc.TestCase.tearDown(self)

  def create_object(self, cls, data):
    res, obj = self.objgen.generate_object(cls, data)
    return obj

  def create_mapping(self, src, dst):
    res, obj = self.objgen.generate_relationship(src, dst)
    return obj

  @classmethod
  def refresh_object(cls, obj):
    """Returns a new instance of a model, fresh and warm from the database."""
    return obj.query.filter_by(id=obj.id).first()

  def test_snapshot_creation(self):
    """Test simple snapshot creation with a simple change"""
    _, creator = self.objgen.generate_person(user_role="Creator")
    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })
    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })

    assessment = self.create_object(models.Assessment, {
        "title": "Test Assessment Snapshot 1"
    })

    self.create_mapping(program, control)
    self.create_mapping(program, assessment)

    control = self.refresh_object(control)

    self.api.modify_object(control, {
        "title": "Test Control Snapshot 1 EDIT 1"
    })

    self.create_object(models.Audit, {
      "title": "Snapshotable audit",
      "program": {"id": program.id},
      "status": "Planned",
      "create-snapshots": True
    })

    self.assertEqual(
      db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")
      ).first().ff_snapshot_enabled,
      True)

    snapshot = db.session.query(models.Snapshot).filter(
      models.Snapshot.child_id == control.id,
      models.Snapshot.child_type == "Control"
    )

    self.assertEqual(snapshot.count(), 1)
    self.assertEqual(snapshot.first().revision.content["title"],
                     "Test Control Snapshot 1 EDIT 1")

  def test_snapshot_creation_with_custom_attribute_values(self):
    pass
