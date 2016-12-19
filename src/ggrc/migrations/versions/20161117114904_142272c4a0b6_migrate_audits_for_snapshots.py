# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Migrate audits for snapshots

Create Date: 2016-11-17 11:49:04.547216
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

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


logger = getLogger(__name__)  # pylint: disable=invalid-name


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
    column("program_id"),
)

programs_table = table(
    "programs",
    column("id"),
    column("context_id")
)


def remove_relationships(connection, event, context_id, user_id, pairs):
  revisions_payload = list()
  relationship_tuple = tuple_(
      relationships_table.c.source_type,
      relationships_table.c.source_id,
      relationships_table.c.destination_type,
      relationships_table.c.destination_id,
  )

  delete_relationships_sql = select([relationships_table]).where(
      relationship_tuple.in_(pairs)
  )
  deleted_relationships = connection.execute(
      delete_relationships_sql).fetchall()

  if deleted_relationships:
    for deleted_rel in deleted_relationships:
      revisions_payload += [{
        "action": "deleted",
        "event_id": event.id,
        "content": dict(deleted_rel),
        "modified_by_id": user_id,
        "resource_id": deleted_rel.id,
        "resource_type": "Relationship",
        "context_id": context_id,
        "source_type": deleted_rel.source_type,
        "source_id": deleted_rel.source_id,
        "destination_type": deleted_rel.destination_type,
        "destination_id": deleted_rel.destination_id,

      }]

    if revisions_payload:
      print "to delete relationship pairs: ", pairs
      connection.execute(revisions_table.insert(), revisions_payload)
      delete_sql = relationships_table.delete().where(
          relationship_tuple.in_(pairs)
      )
      connection.execute(delete_sql)


def create_relationships(connection, event, context_id, user_id, pairs):
  relationships_payload = list()
  revisions_payload = list()

  for pair in pairs:
    relationships_payload += [{
      "source_type": pair[0],
      "source_id": pair[1],
      "destination_type": pair[2],
      "destination_id": pair[3],
      "modified_by_id": user_id,
      "context_id": context_id,
    }]

  if relationships_payload:
    connection.execute(
      relationships_table.insert().prefix_with("IGNORE"),
      relationships_payload)

    created_relationships_sql = select([relationships_table]).where(
      tuple_(
        relationships_table.c.source_type,
        relationships_table.c.source_id,
        relationships_table.c.destination_type,
        relationships_table.c.destination_id,
      ).in_(pairs)
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
        "context_id": context_id,
        "source_type": pair[0],
        "source_id": pair[1],
        "destination_type": pair[2],
        "destination_id": pair[3],

      }]
    if revisions_payload:
      connection.execute(revisions_table.insert(), revisions_payload)


def create_snapshots(connection, event,
                     user_id, audit, objects):
  snapshots_payload = list()
  revisions_payload = list()
  relationship_pairs = set()

  revisions = get_revisions(connection, objects)
  for obj in objects:
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
      logger.warning(
        "Missing revision for object: {}-{}, cannot create snapshot for "
        "Audit-{}".format(obj[0], obj[1], audit.id),
        exc_info=True)

  if snapshots_payload:
    snapshots_insert_sql = snapshots_table.insert().prefix_with(
      "IGNORE")  # TODO remove IGNORE on production run?
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
      relationship_pairs.add((snapshot.child_type,
                              snapshot.child_id, "Snapshot", snapshot.id))

      revisions_payload += [{
        "action": "created",
        "event_id": event.id,
        "content": dict(snapshot),
        "modified_by_id": user_id,
        "resource_id": snapshot.id,
        "resource_type": "Snapshot",
        "context_id": audit.context_id
      }]

    if revisions_payload:
      connection.execute(revisions_table.insert(), revisions_payload)

    if relationship_pairs:
      create_relationships(connection, event, audit.context_id,
                           user_id, relationship_pairs)


def add_objects_to_program_scope(connection, event, user_id,
                                 program_id, program_context_id, objects):
  relationship_pairs = set()

  for obj in objects:
    relationship_pairs.add(("Program", program_id, obj[0], obj[1]))

  create_relationships(connection, event, program_context_id, user_id,
                       relationship_pairs)


def replace_relationships_with_snapshots(connection, event,
                                         user_id, object, audit):
  pass


def clone_dict(obj, data=None, blacklisted=None):
  blacklisted_fields = set()
  if not blacklisted:
    blacklisted_fields = {"id", "context_id", "slug"}

  cpy = dict(obj).copy()
  for bfield in blacklisted_fields:
    if bfield in cpy:
      del cpy[bfield]

  if data:
    cpy.update(data)
  return cpy

object_sql_handlers = {
    "Assessment": {
        "slug_prefix": "ASSESSMENT",
        "insert": assessments_table.insert(),
        "max_id": func.max(assessments_table.c.id),
        "select_slug": select([assessments_table.c.slug]),
        "where_slug": assessments_table.c.slug.in_,
        "select_id": select([assessments_table.c.id]),
        "select_table": select([assessments_table]),
    },
    "Issue": {
        "insert": issues_table.insert(),
        "max_id": "",
    },
    "Request": {
        "insert": requests_table.insert(),
        "max_id": "",
    }
}


def get_slugs(connection, type_, start_id, num):
  slug_prefix = object_sql_handlers[type_]["slug_prefix"]
  slugs = set()

  def generate_slug(x):
    return "{}-{}".format(slug_prefix, x)

  for id_ in xrange(start_id, start_id+num):
    slugs.add(generate_slug(id_))

  conflicting_slugs_sql = object_sql_handlers[type_]["select_slug"].where(
      object_sql_handlers[type_]["where_slug"](slugs)
  )
  conflicting_slugs = connection.execute(conflicting_slugs_sql).fetchall()
  while conflicting_slugs:
    for cslug, in conflicting_slugs:
      slugs.remove(cslug)
      id_ += 1
      slugs.add(generate_slug(id_))

    conflicting_slugs_sql = object_sql_handlers[type_]["select_slug"].where(
        object_sql_handlers[type_]["where_slug"](slugs)
    )
    conflicting_slugs = connection.execute(conflicting_slugs_sql).fetchall()
  return slugs


def duplicate_object(connection, source_type, source_object, objects):
  object_duplicates = list()
  insert_sql = object_sql_handlers[source_type]["insert"]
  max_id = connection.execute(
      object_sql_handlers[source_type]["max_id"]).fetchone()[0]

  slugs = get_slugs(connection, source_type, max_id + 1, len(objects))
  slugs_copy = slugs.copy()

  for object_ in objects:
    data = {
      "context_id": object_.context_id,
      "slug": slugs.pop()
    }
    clone_obj = clone_dict(source_object, data)
    object_duplicates += [clone_obj]

  connection.execute(insert_sql, object_duplicates)
  return slugs_copy


def duplicate_custom_attribute_values(
      connection, source_type, source_object, duplicates):
  custom_attribute_val_duplicates = list()
  source_object_cav_sql = select([custom_attribute_values_table]).where(
    and_(
      custom_attribute_values_table.c.attributable_type == source_type,
      custom_attribute_values_table.c.attributable_id == source_object["id"]
    )
  )
  source_object_cavs = connection.execute(source_object_cav_sql).fetchall()

  # TODO local custom attribute definitions?!
  if source_object_cavs:
    print "source_object_cavs: ", source_object_cavs
    print "duplicates: ", duplicates

    for duplicate in duplicates:
      print duplicate.id
      for source_cav in source_object_cavs:
        print "source_cav: ", source_cav
        data = {
            "attributable_id": duplicate.id,
            "context_id": duplicate.context_id
        }
        clone_cav = clone_dict(source_cav, data)
        custom_attribute_val_duplicates += [clone_cav]

    print "custom_attribute_val_duplicates: ", custom_attribute_val_duplicates
    connection.execute(
        custom_attribute_values_table.insert(),
        custom_attribute_val_duplicates
    )


def duplicate_custom_attribute_definitions(
      connection, source_type, source_object, duplicates):
  custom_attribute_def_duplicates = list()

  source_object_cad_sql = select([custom_attribute_definitions_table]).where(
      and_(
          custom_attribute_definitions_table.c.definition_type == source_type,
          custom_attribute_definitions_table.c.definition_id ==
              source_object["id"],
        )
  )
  source_object_cads = connection.execute(source_object_cad_sql).fetchall()

  if source_object_cads:
    for duplicate in duplicates:
      for source_cad in source_object_cads:
        data = {
            "definition_id": duplicate.id,
            "context_id": duplicate.context_id
        }
        clone_cad = clone_dict(source_cad, data)
        custom_attribute_def_duplicates += [clone_cad]

    connection.execute(
        custom_attribute_definitions_table.insert(),
        custom_attribute_def_duplicates
    )

    duplicate_definitions = {
        (
            dup["definition_id"],
            dup["context_id"],
        )
        for dup in custom_attribute_def_duplicates}
    duplicate_definitions_sql = select([])


def duplicate_revision_chain(connection,
                             source_type, source_object, objects):

  ## TODO DUPLICATE CAV AND CAD HISTORY!
  revision_duplicates = list()

  source_object_revisions_sql = select([revisions_table]).where(
    and_(
      revisions_table.c.resource_type == source_type,
      revisions_table.c.resource_id == source_object["id"]
    )
  )
  source_object_revisions = connection.execute(
      source_object_revisions_sql).fetchall()

  print "source_object_revisions: ", source_object_revisions


def duplicate_object_for_objects(connection,
                                 source_type, source_object, objects):
  # print "duplicate_object_for_objects", source_object, objects

  slugs_of_duplicates = duplicate_object(
      connection, source_type, source_object, objects)

  duplicates = connection.execute(
      object_sql_handlers[source_type]["select_table"].where(
          object_sql_handlers[source_type]["where_slug"](slugs_of_duplicates)
  )).fetchall()

  duplicate_custom_attribute_definitions(
      connection, source_type, source_object, duplicates)
  # duplicate_custom_attribute_values(
  #     connection, source_type, source_object, duplicates
  # )
  # duplicate_revision_chain()



def process_assessment(connection, event, user_id, assessment):
  # print "processing assessment: ", assessment.id
  audit_stubs = get_relationships(connection, "Assessment", assessment.id, {"Audit"})
  if not len(audit_stubs):
    pass
    # logger.warning("No audits found for Assessment-{}".format(assessment.id))
  elif len(audit_stubs) == 1:
    # TODO: just replace relationships?
    pass
    # audit = audits.pop()
    # return replace_relationships_with_snapshots(connection, event,
    #                                             user_id, assessment, audit)
  else:
    # print "\n" * 5
    print "assessment-{} mapped to multiple audits: ".format(assessment.id)
    audit_objects_sql = select([audits_table]).where(
        audits_table.c.id.in_({id_ for _, id_ in audit_stubs})
    )
    audit_objects = connection.execute(audit_objects_sql).fetchall()

    duplicate_object_for_objects(
          connection, "Assessment", assessment, audit_objects)


def get_relationships(connection, type_, id_, filter_types=None):
  if not filter_types:
    relationships = select([relationships_table]).where(and_(
        relationships_table.c.source_type == type_,
        relationships_table.c.source_id == id_,
    )).union(
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
    create_snapshots(connection, event, user_id, audit, audit_scope_objects)
    removal_pairs = {
      ("Audit", audit.id, obj[0], obj[1])
      for obj in audit_scope_objects}
    remove_relationships(
        connection, event, audit.context_id, user_id, removal_pairs)

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

  audits = connection.execute(audits_table.select()).fetchall()

  program_ids = {audit.program_id for audit in audits}

  program_sql = select([programs_table]).where(
      programs_table.c.id.in_(program_ids)
  )
  programs = connection.execute(program_sql)
  program_context = {program.id: program.context_id for program in programs}

  # for audit in audits:
  #   process_audit(
  #       connection, event, user_id, program_context[audit.program_id], audit)

  assessments = connection.execute(assessments_table.select()).fetchall()
  for assessment in assessments:
    process_assessment(connection, event, user_id, assessment)

  raise Exception("blaaaa")


def downgrade():
  pass
