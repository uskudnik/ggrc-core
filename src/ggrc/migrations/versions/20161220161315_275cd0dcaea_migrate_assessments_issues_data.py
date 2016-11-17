# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
migrate-assessments-issues-data

Create Date: 2016-12-20 16:13:15.208946
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from collections import defaultdict
from logging import getLogger
import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import mysql

from sqlalchemy.sql import and_
from sqlalchemy.sql import column
from sqlalchemy.sql import delete
from sqlalchemy.sql import func
from sqlalchemy.sql import select
from sqlalchemy.sql import table
from sqlalchemy.sql import tuple_

from ggrc.models.assessment import Assessment
from ggrc.models.event import Event
from ggrc.models.request import Request
from ggrc.models.issue import Issue
from ggrc.models.relationship import Relationship
from ggrc.models.revision import Revision
from ggrc.models.snapshot import Snapshot

from ggrc.snapshotter.rules import Types

from ggrc.migrations.utils import create_snapshots
from ggrc.migrations.utils import create_relationships
from ggrc.migrations.utils import remove_relationships
from ggrc.migrations.utils import get_migration_user_id
from ggrc.migrations.utils import get_relationships
from ggrc.migrations.utils import get_relationship_cache
from ggrc.migrations.utils import get_revisions
from ggrc.migrations.utils import Stub


logger = getLogger(__name__)  # pylint: disable=invalid-name


# revision identifiers, used by Alembic.
revision = '275cd0dcaea'
down_revision = '142272c4a0b6'

assessments_table = Assessment.__table__
requests_table = Request.__table__
issues_table = Issue.__table__
snapshots_table = Snapshot.__table__
revisions_table = Revision.__table__
relationships_table = Relationship.__table__
events_table = Event.__table__

audits_table = table(
  "audits",
  column("id"),
  column("context_id"),
  column("program_id"),
)

programs_table = table(
  "programs",
  column("id"),
  column("context_id")
)


def process_objects(connection, event, user_id, caches, object_settings):
  relationships_payload = []
  snapshots_payload = []
  revisions_payload = []

  program_relationships = caches["program_rels"]
  audit_relationships = caches["audit_rels"]
  parent_snapshot_cache = caches["snapshots"]
  program_contexts = caches["program_contexts"]
  audit_programs = caches["audit_programs"]
  audit_contexts = caches["audit_contexts"]
  revisions_cache = caches["revisions"]

  object_klass = object_settings["type"]
  object_relationships = object_settings["object_relationships"]
  object_select = object_settings["select_all"]

  all_objects = connection.execute(object_select).fetchall()

  for object_ in all_objects:
    key = Stub(object_klass, object_.id)
    objects = object_relationships[key]
    audit = [x for x in objects if x.type == "Audit"]
    others = [x for x in objects if x.type != "Audit" and x.type in Types.all]

    # TODO remove for production run, we should never have more anything
    # different than one?
    if len(audit) != 1:
      continue

    if audit:
      audit = audit[0]
      others = set(others)

      existing_snapshots = parent_snapshot_cache[audit]
      missing_snapshots = others - existing_snapshots
      if missing_snapshots:
        program_id = audit_programs[audit.id]
        program_ctx_id = program_contexts[program_id]
        audit_context_id = audit_contexts[audit.id]

        for obj_ in missing_snapshots:
          if obj_ in revisions_cache:
            snapshots_payload += [{
              "parent_type": "Audit",
              "parent_id": audit.id,
              "child_type": obj_.type,
              "child_id": obj_.id,
              "revision_id": revisions_cache[obj_],
              "context_id": audit_context_id,
              "modified_by_id": user_id,
            }]
            # TODO this is because of our hack where we rely on relationships
            relationships_payload += [{
              "source_type": "Audit",
              "source_id": audit.id,
              "destination_type": obj_.type,
              "destination_id": obj_.id,
              "modified_by_id": user_id,
              "context_id": audit_context_id,
            }]
          else:
            logger.warning(
                "Missing revision for object {obj.type}-{obj.id}".format(
                obj=obj_
            ))

        missing_from_program_scope = (program_relationships[program_id] -
                                      existing_snapshots)
        if missing_from_program_scope:
          for obj_ in missing_from_program_scope:
            relationships_payload += [{
                "source_type": "Program",
                "source_id": program_id,
                "destination_type": obj_.type,
                "destination_id": obj_.id,
                "modified_by_id": user_id,
                "context_id": program_ctx_id,
            }]

  if snapshots_payload:
    connection.execute(
        snapshots_table.insert().prefix_with("IGNORE"), snapshots_payload)

    snapshot_quadtuples = {
      (snapshot["parent_type"], snapshot["parent_id"],
       snapshot["child_type"], snapshot["child_id"])
      for snapshot in snapshots_payload
      }

    created_snapshots_sql = select([snapshots_table]).where(
      tuple_(
        snapshots_table.c.parent_type,
        snapshots_table.c.parent_id,
        snapshots_table.c.child_type,
        snapshots_table.c.child_id,
      ).in_(snapshot_quadtuples)
    )
    created_snapshots = connection.execute(created_snapshots_sql).fetchall()

    for snapshot in created_snapshots:
      revisions_payload += [{
        "action": "created",
        "event_id": event.id,
        "content": dict(snapshot),
        "modified_by_id": user_id,
        "resource_id": snapshot.id,
        "resource_type": "Snapshot",
        "context_id": snapshot.context_id
      }]

  if relationships_payload:
    connection.execute(
        relationships_table.insert().prefix_with("IGNORE"),
        relationships_payload)


    relationship_quadtuples = {
        (rel["source_type"], rel["source_id"],
         rel["destination_type"], rel["destination_id"])
        for rel in relationships_payload
    }

    created_relationships_sql = select([relationships_table]).where(
        tuple_(
            relationships_table.c.source_type,
            relationships_table.c.source_id,
            relationships_table.c.destination_type,
            relationships_table.c.destination_id,
        ).in_(relationship_quadtuples)
    )

    created_relationships = connection.execute(
        created_relationships_sql).fetchall()

    for relationship in created_relationships:
      revisions_payload += [{
        "action": "created",
        "event_id": event.id,
        "content": dict(relationship),
        "modified_by_id": user_id,
        "resource_id": relationship.id,
        "resource_type": "Relationship",
        "context_id": relationship.context_id
      }]
    connection.execute(revisions_table.insert(), revisions_payload)


def get_scope_snapshots(connection):
  cache = defaultdict(set)

  query = select([snapshots_table])
  result = connection.execute(query)
  for snapshot in result:
    parent = Stub(snapshot.parent_type, snapshot.parent_id)
    child = Stub(snapshot.child_type, snapshot.child_id)
    cache[parent].add(child)
  return cache


def upgrade():
  connection = op.get_bind()

  user_id = get_migration_user_id(connection)

  event = {
    "action": "BULK",
    "resource_id": 0,
    "resource_type": 0,
    "context_id": 0,
    "modified_by_id": user_id
  }
  connection.execute(events_table.insert(), event)

  event_sql = select([events_table]).where(
    events_table.c.action == "BULK").order_by(
    events_table.c.id.desc()).limit(1)
  event = connection.execute(event_sql).fetchone()

  program_sql = select([programs_table])
  programs = connection.execute(program_sql)
  program_contexts = {program.id: program.context_id for program in programs}

  audit_sql = select([audits_table])
  audits = connection.execute(audit_sql).fetchall()
  audit_contexts = {audit.id: audit.context_id for audit in audits}
  audit_programs = {audit.id: audit.program_id for audit in audits}

  program_cache = get_relationship_cache(connection, "Program", Types.all)
  audit_cache = get_relationship_cache(connection, "Audit", Types.all)
  parent_snapshot_cache = get_scope_snapshots(connection)
  assessments_cache = get_relationship_cache(connection, "Assessment",
                                             Types.all | {"Audit"})
  issues_cache = get_relationship_cache(connection, "Issue",
                                        Types.all | {"Audit"})

  all_objects = (program_cache.values() + audit_cache.values() +
                 assessments_cache.values() + issues_cache.values())
  revisionable_objects = all_objects.pop().union(*all_objects)
  revision_cache = get_revisions(connection, revisionable_objects)

  caches = {
    "program_rels": program_cache,
    "audit_rels": audit_cache,
    "snapshots": parent_snapshot_cache,
    "program_contexts": program_contexts,
    "audit_programs": audit_programs,
    "audit_contexts": audit_contexts,
    "revisions": revision_cache
  }

  objects = [
      {
        "type": "Assessment",
        "select_all": assessments_table.select(),
        "object_relationships": assessments_cache
      },
      {
        "type": "Issue",
        "select_all": issues_table.select(),
        "object_relationships": issues_cache
      },
  ]

  for object_settings in objects:
    process_objects(connection, event, user_id, caches, object_settings)


def downgrade():
  pass
