# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test for snapshoter"""

from ggrc import db
import ggrc.models as models
import integration.ggrc
from integration.ggrc import api_helper
import integration.ggrc.generator


class TestSnapshoting(integration.ggrc.TestCase):
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

  @classmethod
  def refresh_object(cls, obj):
    """Returns a new instance of a model, fresh and warm from the database."""
    return obj.query.filter_by(id=obj.id).first()

  def test_snapshot_create(self):
    """Test simple snapshot creation with a simple change"""
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
            models.Audit.title.like(
                "%Snapshotable audit%")).first().ff_snapshot_enabled,
        True)

    snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_id == control.id,
        models.Snapshot.child_type == "Control",
    )

    self.assertEqual(snapshot.count(), 1)
    self.assertEqual(
        snapshot.first().revision.content["title"],
        "Test Control Snapshot 1 EDIT 1")

  def test_snapshot_update(self):
    """Test simple snapshot creation with a simple change"""
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

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).first()
    self.assertEqual(audit.ff_snapshot_enabled, True)

    control_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_id == control.id,
        models.Snapshot.child_type == "Control",
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id)

    self.assertEqual(control_snapshot.count(), 1)
    self.assertEqual(control_snapshot.first().revision.content["title"],
                     "Test Control Snapshot 1 EDIT 1")

    # Create a new objective, add it to program and edit control to detect
    # update.

    objective = self.create_object(models.Objective, {
        "title": "Test Objective Snapshot UNEDITED"
    })
    self.create_mapping(program, objective)

    self.api.modify_object(control, {
        "title": "Test Control Snapshot 1 Edit 2 AFTER initial snapshot"
    })

    audit = self.refresh_object(audit)
    # Initiate update operation
    self.api.modify_object(audit, {
        "update-snapshots": True
    })

    objective_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Objective",
        models.Snapshot.child_id == objective.id,
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id
    )
    self.assertEqual(objective_snapshot.count(), 1)
    self.assertEqual(
        objective_snapshot.first().revision.content["title"],
        "Test Objective Snapshot UNEDITED")

    control_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Control",
        models.Snapshot.child_id == control.id,
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id
    )
    self.assertEqual(control_snapshot.count(), 1)
    self.assertEqual(control_snapshot.first().revision.content["title"],
                     "Test Control Snapshot 1 Edit 2 AFTER initial snapshot")

    control_revisions = db.session.query(models.Revision).filter(
        models.Revision.resource_type == control.type,
        models.Revision.resource_id == control.id)
    self.assertEqual(
        control_revisions.count(), 3,
        "There were 3 edits made at the time")

    self.assertEqual(
        control_revisions.order_by(models.Revision.id.desc()).first().id,
        control_snapshot.one().revision_id)

  def test_snapshot_creation_with_custom_attribute_values(self):
    pass

  def test_creation_of_snapshots_for_multiple_parent_objects(self):
    pass

  def test_large_create(self):
    pass

  def test_large_update(self):
    pass

  def test_individual_update(self):
    pass

  def test_update_when_mapped_objects_are_deleted(self):
    """Test global update when object got deleted or unmapped"""
    pass
