# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Register various listeners needed for snapshot operation"""

from ggrc.services.common import Resource

from ggrc import db
from ggrc import models
from ggrc.login import get_current_user_id
from ggrc.utils import benchmark


from ggrc.snapshotter import create_snapshots
from ggrc.snapshotter import upsert_snapshots
from ggrc.snapshotter import update_snapshot
from ggrc.snapshotter.datastructures import Stub
from ggrc.snapshotter.rules import get_rules
from ggrc.snapshotter.helpers import get_event


def create_all(sender, obj=None, src=None, service=None):  # noqa  # pylint: disable=unused-argument
  """Create snapshots"""
  # TODO REMOVE ON FINAL COMMIT (FEATURE FLAG REMOVAL)
  snapshot_settings = src.get("snapshots")
  if snapshot_settings:
    if snapshot_settings["operation"] == "create":
      with benchmark("Snapshot.register_snapshot_listeners.create"):
        event = get_event(obj, "POST")
      create_snapshots(obj, event)


def upsert_all(sender, obj=None, src=None, service=None):  # noqa  # pylint: disable=unused-argument
  """Update snapshots globally"""
  snapshot_settings = src.get("snapshots")
  if snapshot_settings:
    if snapshot_settings["operation"] == "upsert":
      revisions = {
          (Stub.from_dict(revision["parent"]),
           Stub.from_dict(revision["child"])): revision["revision_id"]
          for revision in snapshot_settings.get("revisions", {})}
      with benchmark("Snapshot.register_snapshot_listeners.create"):
        event = get_event(obj, "PUT")
      upsert_snapshots(obj, event, revisions=revisions)


def update_one(sender, obj=None, src=None, service=None):  # noqa  # pylint: disable=unused-argument
  """Update single snapshot"""
  snapshot_settings = src.get("individual-update")

  if snapshot_settings:
    if snapshot_settings["operation"] == "update":
      event = models.Event(
          modified_by_id=get_current_user_id(),
          action="PUT",
          resource_id=obj.id,
          resource_type=obj.type,
          context_id=obj.context_id)

      db.session.add(event)
      # Because we need event's ID
      db.session.flush()

      update_snapshot(obj, event)


def register_snapshot_listeners():
  """Attach listeners to various models"""

  rules = get_rules()

  # Initialize listening on parent objects
  for type_ in rules.rules.keys():
    model = getattr(models.all_models, type_)
    Resource.model_posted_after_commit.connect(create_all, model, weak=False)
    Resource.model_put_after_commit.connect(upsert_all, model, weak=False)

  Resource.model_put.connect(update_one, models.Snapshot, weak=False)
