# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for snapshotter's preview"""


from flask.json import dumps

from ggrc import db
import ggrc.models as models

from integration.ggrc.snapshotter import SnapshotterBaseTestCase


class TestSnapshotterPreview(SnapshotterBaseTestCase):
  """Test cases for Snapshot Previewer"""

  def setUp(self):
    SnapshotterBaseTestCase.setUp(self)

    self.client.get("/login")
    self.headers = {
        'Content-Type': 'application/json',
        "X-Requested-By": "gGRC",
    }

  def test_create_preview(self):
    pass

  def test_upsert_preview(self):
    # pylint: disable=too-many-locals
    """Test simple snapshot creation with a simple change"""
    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })
    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })
    self.create_mapping(program, control)

    to_edit_1 = [
        (control, "Test Control Snapshot 1 EDIT 1"),
        (control, "Test Control Snapshot 1 EDIT 2"),
    ]
    # control = self.refresh_object(control)
    for obj, new_title in to_edit_1:
      obj = self.refresh_object(obj)
      self.api.modify_object(obj, {
          "title": new_title
      })

    self.create_audit(program)

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).first()
    self.assertEqual(audit.ff_snapshot_enabled, True)

    # Create a new objective, add it to program and edit control to detect
    # update.

    objective = self.create_object(models.Objective, {
        "title": "Test Objective Snapshot UNEDITED"
    })
    self.create_mapping(program, objective)

    control = self.refresh_object(control)
    objective = self.refresh_object(objective)
    to_edit_2 = [
        (control, "Test Control Snapshot 1 EDIT 3 AFTER initial snapshot"),
        (control, "Test Control Snapshot 1 EDIT 4 AFTER initial snapshot"),
        (objective, "Test Objective Snapshot 1 EDIT 1 AFTER initial snapshot")
    ]
    for obj, new_title in to_edit_2:
      obj = self.refresh_object(obj)
      self.api.modify_object(obj, {
          "title": new_title
      })
    del obj

    data = {
        "snapshotter": {
            "parent": self.objgen.create_stub(audit),
            "operation": "upsert"
        }
    }

    response = self.client.get("/_service/snapshotter/preview",
                               data=dumps(data), headers=self.headers)

    self.assertEqual(response.status_code, 200)

    data = response.json
    for key in {"created", "updated", "history"}:
      self.assertIn(key, data)

    created = data["created"]
    updated = data["updated"]

    self.assertIn("Audit", created)
    self.assertIn("Audit", updated)
    self.assertIn(str(audit.id), created["Audit"])
    self.assertIn(str(audit.id), updated["Audit"])
    created_audit = created["Audit"][str(audit.id)]
    updated_audit = updated["Audit"][str(audit.id)]

    control_revisions = db.session.query(models.Revision).filter(
        models.Revision.resource_type == "Control",
        models.Revision.resource_id == control.id
    ).all()

    objective_revisions = db.session.query(models.Revision).filter(
        models.Revision.resource_type == "Objective",
        models.Revision.resource_id == objective.id
    ).all()

    self.assertEqual(
        created_audit[0]["revision_id"], objective_revisions[-1].id)

    self.assertEqual(
        updated_audit[0]["revision_id"], control_revisions[-1].id)

    base_edits = [
        (control, "Test Control Snapshot 1"),
        (objective, "Test Objective Snapshot UNEDITED")]

    edits = base_edits + to_edit_1 + to_edit_2
    control_edits = [title for obj, title in edits if obj.type == "Control"]
    objective_edits = [title
                       for obj, title in edits if obj.type == "Objective"]

    control_history = data["history"]["Control"][str(control.id)]
    objective_history = data["history"]["Objective"][str(objective.id)]

    edits_history = [
        (control_edits, control_history),
        (objective_edits, objective_history)
    ]
    for edits, history in edits_history:
      for title, edit in zip(edits, history):
        revid, modified_date, rev_content = edit  # noqa # pylint: disable=unused-variable
        self.assertEqual(title, rev_content["title"])

  def test_individual_update_preview(self):
    pass
