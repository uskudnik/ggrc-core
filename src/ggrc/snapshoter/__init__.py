# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import logging

from sqlalchemy import and_

from ggrc import db
from ggrc import models

from ggrc.login import get_current_user

from ggrc.automapper.rules import Attr

from ggrc.snapshoter.rules import rules

from ggrc.services.common import Resource


class SnapshotGenerator(object):
  def __init__(self):
    pass

  def _get_snapshotable_objects(self, obj):
    object_rules = rules.rules[obj.type]

    related_mappings = obj.related_objects({
        rule for rule in object_rules["fst"] if isinstance(rule, basestring)})

    direct_mappings = {getattr(obj, rule.name)
                       for rule in object_rules["fst"] if isinstance(rule, Attr)}

    related_objects = related_mappings | direct_mappings

    return set([sndobj
                for fstobj in related_objects
                for sndobj in fstobj.related_objects(object_rules["snd"])])


  def generate_snapshots(self, obj):
    print "generate_snapshots"

    snapshotable_objects = self._get_snapshotable_objects(obj)

    print snapshotable_objects

    # import ipdb;
    # ipdb.set_trace()
    #

    # TODO create a single or/union + and?
    for sobj in snapshotable_objects:
      print "sobj: ", sobj.type, sobj.id

      revision = db.session.query(models.Revision).filter(
        and_(
          models.Revision.resource_type == sobj.type,
          models.Revision.resource_id == sobj.id
        )
      ).order_by(models.Revision.id.desc()).first()

      print revision
      # import ipdb;
      # ipdb.set_trace()
      # TODO there are objects without revisions, what do we want
      # TODO do with them?
      if revision:
        snapshot = models.Snapshot(
          parent_id=obj.id,
          parent_type=obj.type,
          child_id=sobj.id,
          child_type=sobj.type,
          revision=revision,
          modified_by=get_current_user(),
          context=obj.context
        )
        print snapshot
        db.session.add(snapshot)


def register_snapshot_listeners():
  print "register_snapshot_listeners"

  def initialize_snapshots(sender, obj=None, src=None, service=None):
    print "initialize_snapshots"
    # TODO REMOVE ON FINAL COMMIT (FEATURE FLAG REMOVAL)
    if src.get("create-snapshots"):
      print "\n"*5
      print "connect CREATE SNAPSHOTS INSTAD OF RELATIONSHIPS"
      obj.ff_snapshot_enabled = True
      db.session.add(obj)
      SnapshotGenerator().generate_snapshots(obj)

  for type_ in rules.rules.keys():
    model = getattr(models.all_models, type_)
    Resource.model_posted_after_commit.connect(initialize_snapshots, model, weak=False)


# def reccon(sender, **kw):
#   print "sender: ", sender
#   print "kws: ", kw
#
# blinker.receiver_connected.connect(reccon)
