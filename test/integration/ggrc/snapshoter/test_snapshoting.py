# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test for snapshoter"""

import collections
from os.path import abspath, dirname, join

from ggrc import db
import ggrc.models as models
import integration.ggrc
from integration.ggrc import api_helper
import integration.ggrc.generator
from integration.ggrc.converters import TestCase
from ggrc.snapshoter.rules import Types


THIS_ABS_PATH = abspath(dirname(__file__))
CSV_DIR = join(THIS_ABS_PATH, "../converters/test_csvs/")


class TestSnapshoting(TestCase):
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
        "snapshots": {
            "operation": "create"
        }
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

    snapshot_revision = db.session.query(
        models.Revision.resource_type,
        models.Revision.resource_id,
        models.Revision.content
    ).filter(
        models.Revision.resource_type == "Snapshot",
        models.Revision.resource_id == snapshot.first().id,
    )

    self.assertEqual(snapshot_revision.count(), 1)
    snapshot_revision_content = snapshot_revision.first()[2]
    self.assertEqual(snapshot_revision_content["child_type"], "Control")
    self.assertEqual(snapshot_revision_content["child_id"], control.id)

    relationship_columns = db.session.query(models.Relationship)
    relationship = relationship_columns.filter(
        models.Relationship.source_type == "Control",
        models.Relationship.source_id == control.id,
        models.Relationship.destination_type == "Snapshot",
        models.Relationship.destination_id == snapshot.first().id
    ).union(
        relationship_columns.filter(
            models.Relationship.source_type == "Snapshot",
            models.Relationship.source_id == snapshot.first().id,
            models.Relationship.destination_type == "Control",
            models.Relationship.destination_id == control.id
        )
    )
    self.assertEqual(relationship.count(), 1)

    relationship_revision = db.session.query(
        models.Revision.resource_type,
        models.Revision.resource_id,
        models.Revision.content,
    ).filter(
        models.Revision.resource_type == "Relationship",
        models.Revision.resource_id == relationship.first().id,
    )
    self.assertEqual(relationship_revision.count(), 1)

  def test_snapshot_update(self):
    """Test simple snapshot creation with a simple change"""
    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })
    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })

    self.create_mapping(program, control)

    control = self.refresh_object(control)

    self.api.modify_object(control, {
        "title": "Test Control Snapshot 1 EDIT 1"
    })

    self.create_object(models.Audit, {
        "title": "Snapshotable audit",
        "program": {"id": program.id},
        "status": "Planned",
        "snapshots": {
            "operation": "create",
        }
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
        "snapshots": {
            "operation": "upsert"
        }
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

  def test_update_to_specific_version(self):
    """Test global update and selecting a specific revision for one object"""
    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })
    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })

    objective = self.create_object(models.Objective, {
        "title": "Test Objective Snapshot 1"
    })

    self.create_mapping(program, control)
    self.create_mapping(program, objective)

    control = self.refresh_object(control)
    for x in xrange(1, 4):
      self.api.modify_object(control, {
          "title": "Test Control Snapshot 1 EDIT {}".format(x)
      })

    self.create_object(models.Audit, {
        "title": "Snapshotable audit",
        "program": {"id": program.id},
        "status": "Planned",
        "snapshots": {
            "operation": "create"
        }
    })

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).first()
    self.assertEqual(audit.ff_snapshot_enabled, True)

    revision = db.session.query(
        models.Revision.id,
        models.Revision.resource_type,
        models.Revision.resource_id,
        models.Revision.content,
    ).filter(
        models.Revision.resource_type == control.type,
        models.Revision.resource_id == control.id,
        models.Revision.content.like("%Test Control Snapshot 1 EDIT 2%"),
    ).one()

    audit = self.refresh_object(audit)
    self.api.modify_object(audit, {
        "snapshots": {
            "operation": "upsert",
            "revisions": [{
                "parent": self.objgen.create_stub(audit),
                "child": self.objgen.create_stub(control),
                "revision_id": revision[0]
            }]
        }
    })

    control_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == control.type,
        models.Snapshot.child_id == control.id,
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id
    )
    self.assertEqual(control_snapshot.count(), 1)
    self.assertEqual(control_snapshot.first().revision.content["title"],
                     "Test Control Snapshot 1 EDIT 2")

  def test_snapshot_creation_with_custom_attribute_values(self):
    pass

  def test_creation_of_snapshots_for_multiple_parent_objects(self):
    pass

  def test_individual_update(self):
    """Test update of individual snapshot

    1. Create program with mapped control and data asset.
    2. Create audit, verify there are snapshot for control and data asset
    3. Update control and data asset title
    4. Run refresh on control's snapshot object
    5. Verify control's title is changed and data assets NOT
    """

    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })

    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })
    data_asset = self.create_object(models.DataAsset, {
        "title": "Test DataAsset Snapshot 1"
    })

    self.create_mapping(program, control)
    self.create_mapping(program, data_asset)

    control = self.refresh_object(control)
    data_asset = self.refresh_object(data_asset)

    self.create_object(models.Audit, {
        "title": "Snapshotable audit",
        "program": {"id": program.id},
        "status": "Planned",
        "snapshots": {
            "operation": "create",
        }
    })

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).first()

    self.assertEqual(audit.ff_snapshot_enabled, True)

    self.assertEqual(
        db.session.query(models.Snapshot).filter(
            models.Snapshot.parent_type == "Audit",
            models.Snapshot.parent_id == audit.id).count(),
        2)

    control = self.refresh_object(control)
    self.api.modify_object(control, {
        "title": "Test Control Snapshot 1 EDIT 1"
    })

    data_asset = self.refresh_object(data_asset)
    self.api.modify_object(data_asset, {
        "title": "Test Data Asset Snapshot 1 EDIT 1"
    })

    control_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Control",
        models.Snapshot.child_id == control.id).first()

    self.assertEqual(
        control_snapshot.revision.content["title"],
        "Test Control Snapshot 1")

    self.api.modify_object(control_snapshot, {
        "individual-update": {
            "operation": "update"
        }
    })

    expected = [
        (control, "Test Control Snapshot 1 EDIT 1"),
        (data_asset, "Test DataAsset Snapshot 1"),
    ]
    for obj, expected_title in expected:
      snapshot = db.session.query(models.Snapshot).filter(
          models.Snapshot.child_type == obj.__class__.__name__,
          models.Snapshot.child_id == obj.id).first()
      self.assertEquals(
          snapshot.revision.content["title"],
          expected_title)

    control_snapshot_event = db.session.query(models.Event).filter(
        models.Event.resource_type == "Snapshot",
        models.Event.resource_id == control_snapshot.id,
        models.Event.action == "PUT"
    )
    self.assertEqual(control_snapshot_event.count(), 1)

    control_snapshot_revisions = db.session.query(models.Revision).filter(
        models.Revision.resource_type == "Snapshot",
        models.Revision.resource_id == control_snapshot.id
    )
    self.assertEqual(control_snapshot_revisions.count(), 2)

  def test_update_when_mapped_objects_are_deleted(self):
    """Test global update when object got deleted or unmapped"""
    pass

  def test_snapshoting_of_objects(self):
    """Test that all object types that should be snapshotted are snapshotted

    It is expected that all objects will be triplets.
    """

    self._import_file("snapshotter_create.csv")

    # Verify that all objects got imported correctly.
    for _type in Types.all:
      self.assertEqual(
          db.session.query(getattr(models.all_models, _type)).count(),
          3)

    program = db.session.query(models.Program).filter(
        models.Program.slug == "Prog-13211"
    ).one()

    self.create_object(models.Audit, {
        "title": "Snapshotable audit",
        "program": {"id": program.id},
        "status": "Planned",
        "snapshots": {
            "operation": "create",
        }
    })

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).first()

    snapshots = db.session.query(models.Snapshot).filter(
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id,
    )

    self.assertEqual(snapshots.count(), len(Types.all) * 3)

    type_count = collections.defaultdict(int)
    for snapshot in snapshots:
      type_count[snapshot.child_type] += 1

    missing_types = set()
    for snapshottable_type in Types.all:
      if type_count[snapshottable_type] != 3:
        missing_types.add(snapshottable_type)

    self.assertEqual(missing_types, set())
