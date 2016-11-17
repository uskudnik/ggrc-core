# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Migrations Utility Module.

Place here your migration helpers that is shared among number of migrations.

"""

from collections import namedtuple
from logging import getLogger

from sqlalchemy.sql import and_
from sqlalchemy.sql import column
from sqlalchemy.sql import delete
from sqlalchemy.sql import func
from sqlalchemy.sql import select
from sqlalchemy.sql import table
from sqlalchemy.sql import tuple_

from ggrc.models.relationship import Relationship
from ggrc.models.revision import Revision
from ggrc.models.snapshot import Snapshot

relationships_table = Relationship.__table__
revisions_table = Revision.__table__
snapshots_table = Snapshot.__table__


Stub = namedtuple("Stub", ["type", "id"])

logger = getLogger(__name__)  # pylint: disable=invalid-name


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
      child = Stub(obj.destination_type, obj.destination_id)
    else:
      child = Stub(obj.source_type, obj.source_id)
    related.add(child)
  return related


def get_relationship_cache(connection, type_, filter_types=None):
  if not filter_types:
    relationships = select([relationships_table]).where(and_(
      relationships_table.c.source_type == type_,
      )).union(
      select([relationships_table]).where(and_(
        relationships_table.c.destination_type == type_,
        ))
    )
  else:
    relationships = select([relationships_table]).where(and_(
      relationships_table.c.source_type == type_,
      relationships_table.c.destination_type.in_(filter_types)
    )
    ).union(
      select([relationships_table]).where(and_(
        relationships_table.c.destination_type == type_,
        relationships_table.c.source_type.in_(filter_types)
      ))
    )

  relationships_ = connection.execute(relationships)
  from collections import defaultdict
  cache = defaultdict(set)
  for obj in relationships_:
    if obj.source_type == type_:
      source = Stub(obj.source_type, obj.source_id)
      target = Stub(obj.destination_type, obj.destination_id)
    else:
      source = Stub(obj.destination_type, obj.destination_id)
      target = Stub(obj.source_type, obj.source_id)
    cache[source].add(target)
  return cache


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


def get_revisions(connection, objects):
  # print "getting revisions: ", objects

  revisions = select([
    func.max(revisions_table.c.id),
    revisions_table.c.resource_type,
    revisions_table.c.resource_id,
  ]).where(
    tuple_(
      revisions_table.c.resource_type,
      revisions_table.c.resource_id).in_(objects)
  ).group_by(revisions_table.c.resource_type, revisions_table.c.resource_id)
  revisions_ = {Stub(rtype, rid): id_ for id_, rtype, rid in
                connection.execute(revisions).fetchall()}
  return revisions_


def create_snapshots(connection, event,
                     user_id, audit, audit_context_id, objects):
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
        "context_id": audit_context_id,
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

    # TODO remove this if no longer needed when child property is merged
    for snapshot in created_snapshots:
      relationship_pairs.add(
        (snapshot.parent_type, snapshot.parent_id,
         snapshot.child_type, snapshot.child_id))

      revisions_payload += [{
        "action": "created",
        "event_id": event.id,
        "content": dict(snapshot),
        "modified_by_id": user_id,
        "resource_id": snapshot.id,
        "resource_type": "Snapshot",
        "context_id": audit_context_id
      }]

    if revisions_payload:
      connection.execute(revisions_table.insert(), revisions_payload)

    if relationship_pairs:
      create_relationships(connection, event, audit_context_id,
                           user_id, relationship_pairs)


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
