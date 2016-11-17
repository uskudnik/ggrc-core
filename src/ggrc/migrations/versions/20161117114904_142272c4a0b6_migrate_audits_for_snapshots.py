# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Migrate audits for snapshots

Create Date: 2016-11-17 11:49:04.547216
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from logging import getLogger

from alembic import op

from sqlalchemy.sql import and_
from sqlalchemy.sql import column
from sqlalchemy.sql import func
from sqlalchemy.sql import select
from sqlalchemy.sql import table

from ggrc.models.event import Event
from ggrc.models.relationship import Relationship

from ggrc.migrations.utils import create_snapshots
from ggrc.migrations.utils import create_relationships
from ggrc.migrations.utils import remove_relationships
from ggrc.migrations.utils import get_migration_user_id
from ggrc.migrations.utils import get_relationships

from ggrc.snapshotter.rules import Types


logger = getLogger(__name__)  # pylint: disable=invalid-name


# revision identifiers, used by Alembic.
revision = '142272c4a0b6'
down_revision = '587e41a1593d'

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


def add_objects_to_program_scope(connection, event, user_id,
                                 program_id, program_context_id, objects):
  relationship_pairs = set()

  for obj in objects:
    relationship_pairs.add(("Program", program_id, obj[0], obj[1]))

  create_relationships(connection, event, program_context_id, user_id,
                       relationship_pairs)


def process_audit(connection, event, user_id, program_context_id, audit):
  print "processing audit ", audit.id
  audit_scope_objects = get_relationships(
      connection, "Audit", audit.id, Types.all)
  program_scope_objects = get_relationships(
      connection, "Program", audit.program_id, Types.all)

  missing_in_program_scope = audit_scope_objects - program_scope_objects

  if missing_in_program_scope:
    add_objects_to_program_scope(
        connection, event, user_id,
        audit.program_id, program_context_id, missing_in_program_scope)

  if audit_scope_objects:
    create_snapshots(
        connection, event, user_id,
        audit, audit.context_id, audit_scope_objects)
    # TODO we probably shouldn't remove relationships since we still rely on
    # them as a hack
    # removal_pairs = {
    #     ("Audit", audit.id, obj[0], obj[1])
    #     for obj in audit_scope_objects}
    # remove_relationships(
    #     connection, event, audit.context_id, user_id, removal_pairs)


def validate_database(connection):
  audits_more = []
  ghost_objects = []

  tables = [
      "Assessment",
      "Issue",
  ]

  for klass_name in tables:
    sql_base_left = select([
        func.count(relationships_table.c.id).label("relcount"),
        relationships_table.c.destination_id.label("audit_id"),
    ]).where(
        and_(
            relationships_table.c.source_type == klass_name,
            relationships_table.c.destination_type == "Audit"
        )
    ).group_by(relationships_table.c.destination_id)

    sql_base_right = select([
        func.count(relationships_table.c.id).label("relcount"),
        relationships_table.c.source_id.label("audit_id"),
    ]).where(
        and_(
            relationships_table.c.destination_type == klass_name,
            relationships_table.c.source_type == "Audit"
        )
    ).group_by(relationships_table.c.source_id)

    sql_left_more = sql_base_left.having(sql_base_left.c.relcount > 1)
    sql_right_more = sql_base_right.having(sql_base_right.c.relcount > 1)
    sql_left_none = sql_base_left.having(sql_base_left.c.relcount == 0)
    sql_right_none = sql_base_right.having(sql_base_right.c.relcount == 0)

    result_left_more = connection.execute(sql_left_more).fetchall()
    result_right_more = connection.execute(sql_right_more).fetchall()
    result_more = result_left_more + result_right_more

    result_left_none = connection.execute(sql_left_none).fetchall()
    result_right_none = connection.execute(sql_right_none).fetchall()
    result_none = result_left_none + result_right_none

    if result_more:
      audits_more += [(klass_name, result_more)]
    if result_none:
      ghost_objects += [(klass_name, result_none)]
  return audits_more, ghost_objects


def upgrade():
  """Migrate audit-related data and concepts to audit snapshots"""
  connection = op.get_bind()

  audits_more, ghost_objects = validate_database(connection)

  corrupted_audit_ids = set()

  if audits_more or ghost_objects:
    for klass_name, result in audits_more:
      ids = [id_ for _, id_ in result]
      corrupted_audit_ids = corrupted_audit_ids.union(set(ids))
      print "The following Audits have more than one {klass}: {ids}".format(
          klass=klass_name,
          ids=",".join(map(str, ids))
      )
    for klass_name, result in ghost_objects:
      ids = [id_ for _, id_ in result]
      corrupted_audit_ids = corrupted_audit_ids.union(set(ids))
      print "The following {klass} have no Audits mapped to them: {ids}".format(
        klass=klass_name,
        ids=",".join(map(str, ids))
      )

    # TODO decide if we want to block migration before bigger mess is created
    # accidentally
    # raise Exception("Cannot perform migration.")

  # TODO add MIGRATOR support
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

  audits = connection.execute(audits_table.select()).fetchall()

  program_ids = {audit.program_id for audit in audits}

  program_sql = select([programs_table]).where(
      programs_table.c.id.in_(program_ids)
  )
  programs = connection.execute(program_sql)
  program_contexts = {program.id: program.context_id for program in programs}

  for audit in audits:
    if audit.id not in corrupted_audit_ids:
      print "processing uncorrupted audit: ID ", audit.id
      process_audit(
          connection, event, user_id,
          program_contexts[audit.program_id], audit)


def downgrade():
  pass
