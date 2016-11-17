# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Migrate audits for snapshots

Create Date: 2016-11-17 11:49:04.547216
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import mysql

from sqlalchemy.sql import and_
from sqlalchemy.sql import column
from sqlalchemy.sql import func
from sqlalchemy.sql import select
from sqlalchemy.sql import table
from sqlalchemy.sql import tuple_

from ggrc.models.audit import Audit
from ggrc.models.assessment import Assessment
from ggrc.models.event import Event
from ggrc.models.request import Request
from ggrc.models.issue import Issue
from ggrc.models.relationship import Relationship
from ggrc.models.revision import Revision
from ggrc.models.custom_attribute_definition import CustomAttributeDefinition
from ggrc.models.custom_attribute_value import CustomAttributeValue
from ggrc.models.snapshot import Snapshot

from ggrc.snapshotter.rules import Types


# revision identifiers, used by Alembic.
revision = '142272c4a0b6'
down_revision = '2a5a39600741'

assessments_table = Assessment.__table__
requests_table = Request.__table__
issues_table = Issue.__table__
custom_attribute_definitions_table = CustomAttributeDefinition.__table__
custom_attribute_values_table = CustomAttributeValue.__table__
snapshots_table = Snapshot.__table__
revisions_table = Revision.__table__
relationships_table = Relationship.__table__
events_table = Event.__table__

audits_table = table(
    "audits",
    column("id"),
    column("context_id"),
)


def create_snapshots():
  pass


def process_assessment():
  pass


def get_relationships(connection, type_, id_, filter_types=None):
  if not filter_types:
    relationships = select([relationships_table]).where(and_(
      relationships_table.c.source_type == type_,
      relationships_table.c.source_id == id_,
    )
    ).union(
      select([relationships_table]).where(and_(
        relationships_table.c.destination_type == type_,
        relationships_table.c.destination_id == id_,
      ))
    )
  else:
    relationships = select([relationships_table]).where(and_(
        relationships_table.c.source_type == type_,
        relationships_table.c.source_id == id_,
        relationships_table.c.destination_type.in_(filter_types)
      )
    ).union(
        select([relationships_table]).where(and_(
            relationships_table.c.destination_type == type_,
            relationships_table.c.destination_id == id_,
            relationships_table.c.source_type.in_(filter_types)
        ))
    )

  relationships_ = connection.execute(relationships)
  related = set()
  for obj in relationships_:
    if obj.source_type == type_ and obj.source_id == id_:
      child = (obj.destination_type, obj.destination_id)
    else:
      child = (obj.source_type, obj.source_id)
    related.add(child)
  return related


def get_revisions(connection, objects):
  revisions = select([
    func.max(revisions_table.c.id),
    revisions_table.c.resource_type,
    revisions_table.c.resource_id,
  ]).where(
      tuple_(
          revisions_table.c.resource_type,
          revisions_table.c.resource_id).in_(objects)
  ).group_by(revisions_table.c.resource_type, revisions_table.c.resource_id)
  revisions_ = {(rtype, rid): id_ for id_, rtype, rid in
                connection.execute(revisions).fetchall()}
  return revisions_


def get_migration_user_id(connection, role_name="Administrator"):
  from ggrc_basic_permissions.models import UserRole
  from ggrc_basic_permissions.models import Role

  roles_table = Role.__table__
  user_roles_table = UserRole.__table__

  admin_role_sql = select([roles_table.c.id]).where(
      roles_table.c.name == role_name)
  admin_role = connection.execute(admin_role_sql).fetchone()[0]

  user_role_sql = select([user_roles_table]).where(
      user_roles_table.c.role_id == admin_role
  ).order_by(user_roles_table.c.person_id).limit(1)
  return connection.execute(user_role_sql).fetchone().person_id


def get_migration_user(connection):
  from ggrc.models.person import Person
  admin_id = get_migration_user_id(connection).id
  return Person.query.get(admin_id)


def process_audit(connection, event, user_id, audit):
  print "processing audit ", audit.id
  scope_objects = get_relationships(connection, "Audit", audit.id, Types.all)
  snapshots_payload = list()
  relationships_payload = list()
  revisions_payload = list()

  if scope_objects:
    revisions = get_revisions(connection, scope_objects)
    for obj in scope_objects:
      if obj in revisions and revisions[obj]:
        snapshots_payload += [{
          "parent_type": "Audit",
          "parent_id": audit.id,
          "child_type": obj[0],
          "child_id": obj[1],
          "revision_id": revisions[obj],
          "context_id": audit.context_id,
          "modified_by_id": user_id,  # TODO verify
        }]
      else:
        print "MISSING REVISION: ", obj

    if snapshots_payload:
      snapshots_insert_sql = snapshots_table.insert().prefix_with("IGNORE")  # TODO remove IGNORE on production run?
      connection.execute(snapshots_insert_sql, snapshots_payload)

      pairs = {
          ("Audit", audit.id, snapshot["child_type"], snapshot["child_id"])
          for snapshot in snapshots_payload}

      created_snapshots_sql = select([snapshots_table]).where(
          tuple_(
              snapshots_table.c.parent_type,
              snapshots_table.c.parent_id,
              snapshots_table.c.child_type,
              snapshots_table.c.child_id,
          ).in_(pairs)
      )
      created_snapshots = connection.execute(created_snapshots_sql).fetchall()

      for snapshot in created_snapshots:
        relationships_payload += [{
            "source_type": snapshot.child_type,
            "source_id": snapshot.child_id,
            "destination_type": "Snapshot",
            "destination_id": snapshot.id,
            "modified_by_id": user_id,
            "context_id": audit.context_id,
        }]

        revisions_payload += [{
          "action": "created",
          "event_id": event.id,
          "content": dict(snapshot),
          "modified_by_id": user_id,
          "resource_id": snapshot.id,
          "resource_type": "Snapshot",
          "context_id": audit.context_id
        }]

      if relationships_payload:
        connection.execute(
            relationships_table.insert().prefix_with("IGNORE"),
          relationships_payload)

        relationship_pairs = {
            (relationship["source_type"], relationship["source_id"],
             relationship["destination_type"], relationship["destination_id"])
            for relationship in relationships_payload}
        created_relationships_sql = select([relationships_table]).where(
            tuple_(
                relationships_table.c.source_type,
                relationships_table.c.source_id,
                relationships_table.c.destination_type,
                relationships_table.c.destination_id,
            ).in_(relationship_pairs)
        )
        created_relationships = connection.execute(
            created_relationships_sql).fetchall()

        for created_rel in created_relationships:
          revisions_payload += [{
            "action": "created",
            "event_id": event.id,
            "content": dict(created_rel),
            "modified_by_id": user_id,
            "resource_id": created_rel.id,
            "resource_type": "Relationship",
            "context_id": audit.context_id
          }]

      if revisions_payload:
        connection.execute(revisions_table.insert(), revisions_payload)


def upgrade():
  """Migrate audit-related data and concepts to audit snapshots

  Target of data migration:
  * Assessments, Requests and Issues that are mapped to multiple audits need to
    be duplicated and mapped to each individual audit
      * We also need to duplicate custom attribute values and custom
        attribute definitions
      * Convert relationships to objects to relationships to
        snapshots
      * Duplicate relationships and relationship attributes to persons
      * Duplicate comments
      * Duplicate relationships to evidences
      * Duplicate URLs
      * Duplicate revision history of assessment/req/issue
      * Duplicate custom attribute definition/value and relationship revisions
      * Duplicate user roles
  * Instead of relationships to snapshottable objects, every object has
    snapshots of existing audit-object relationships ONLY (verify with akhil)
      -- snapshot audit scopes not audit's program scope
  * If assessments/request/issues are done on objects that are not snapshotted
    in audit scope, we create relationships to audit programs and create
    snapshots of those objects in scope of audit
  * Who is (default) user? Whoever created audit/assessment or do we set some
    default admin user?

  """
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

  audits_result = connection.execute(audits_table.select())

  for audit in audits_result:
    process_audit(connection, event, user_id, audit)

  assessments_result = connection.execute(assessments_table.select()).fetchall()
  for assessment in assessments_result:
    process_assessment(connection, assessment)

  raise Exception("blaaaa")


def downgrade():
  pass
