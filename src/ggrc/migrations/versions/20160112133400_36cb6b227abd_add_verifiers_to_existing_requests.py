# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

"""Add verifiers to existing requests

Revision ID: 36cb6b227abd
Revises: 297131e22e28
Create Date: 2016-01-12 13:34:00.388880

"""

# revision identifiers, used by Alembic.
from collections import defaultdict

revision = '36cb6b227abd'
down_revision = '297131e22e28'

from alembic import op
from sqlalchemy import Integer
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.sql import column
from sqlalchemy.sql import func
from sqlalchemy.sql import table
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql.expression import select

requests_table = table(
    'requests',
    column('id'),
    column('audit_id'),
    column('status')
)


audits_table = table(
    'audits',
    column('id'),
    column('context_id'),
    column('contact_id'),
    column('program_id'),
)


programs_table = table(
    'programs',
    column('id'),
    column('context_id'),
)


user_roles_table = table(
    'user_roles',
    column('role_id'),
    column('context_id'),
    column('person_id'),
)


roles_table = table(
    'roles',
    column('id'),
    column('name'),
)


relationships_table = table(
    'relationships',
    column('id'),
    column('context_id'),
    column('source_id'),
    column('source_type'),
    column('destination_id'),
    column('destination_type'),
)

relationship_attrs_table = table(
    'relationship_attrs',
    column('relationship_id'),
    column('attr_name'),
    column('attr_value'),
)


def build_bulk_insert_people_object(relationship_id, context_id, reqid, pid):
  return {
      "id": relationship_id,
      "context_id": context_id,
      "source_type": "Request",
      "source_id": reqid,
      "destination_type": "Person",
      "destination_id": pid
  }


def build_bulk_insert_rel_attr_object(rel_id, attr_value):
  return {
      "relationship_id": rel_id,
      "attr_name": "AssigneeType",
      "attr_value": ",".join(attr_value)
  }


def get_requests_for_processing(connection, status):
  """Get requests in certain state"""
  return {rid[0] for rid in connection.execute(
      select([requests_table.c.id]).where(
          requests_table.c.status == status)
  ).fetchall()}


def _get_max_relationship_id(connection):
  max_relationship_id = connection.execute(
      select([func.max(relationships_table.c.id, type_=Integer)])).scalar()
  if max_relationship_id:
    return max_relationship_id
  else:
    return 0


def get_auditors_contexts(connection):
  """Returns all contexts where at least one person is auditor and returns a
  list of all auditors for that context.
  {
    [context_id]: [person_id 1, person_id 2, ...]
  }
  """
  try:
    s = select(
        [user_roles_table.c.context_id,
         user_roles_table.c.person_id]).select_from(
        user_roles_table.join(roles_table,
                              user_roles_table.c.role_id == roles_table.c.id)
    ).where(roles_table.c.name == "Auditor")
    context_audit_select = connection.execute(s)
  except ProgrammingError:
    # On empty database, user_roles table doesn't exist yet,
    # ggrc_basic_permissions module creates it
    return {}

  contexts = defaultdict(list)
  for ctxid, person_id in context_audit_select:
    contexts[ctxid] += [person_id]
  return contexts


def get_programowners_contexts(connection):
  """
  Returns all contexts where at least one person is program owner and returns a
  list of all program owners for that context.
  """
  try:
    context_audit_select = [(ctxid, person_id) for roleid, ctxid, person_id in
                            connection.execute(user_roles_table.select().where(
                                user_roles_table.c.role_id == 1)).fetchall()]
  except ProgrammingError:
    return {}

  contexts = defaultdict(list)
  for ctxid, person_id in context_audit_select:
    contexts[ctxid] += [person_id]
  return contexts


def get_requests_with_no_attr(connection, attr_value):
  """Returns a list of all Final/Verified requests that don't have at least one
   person with `attr_value` specified as relationship_attr for request - person
   relationships.
  """
  s = select([requests_table.c.id,
              relationships_table,
              relationship_attrs_table.c.relationship_id,
              relationship_attrs_table.c.attr_value]).select_from(
      requests_table.join(relationships_table, or_(and_(
          relationships_table.c.source_type == "Request",
          relationships_table.c.source_id == requests_table.c.id,
          relationships_table.c.destination_type == "Person"
      ),
          and_(
          relationships_table.c.destination_type == "Request",
          relationships_table.c.destination_id == requests_table.c.id,
          relationships_table.c.source_type == "Person"
      )
      )).join(relationship_attrs_table,
              relationship_attrs_table.c.relationship_id ==
              relationships_table.c.id)
  ).where(requests_table.c.status.in_(["Final", "Verified"]))

  result = connection.execute(s).fetchall()

  #  requests.id,
  #  relationships.id,
  #  relationships.context_id,
  #  relationships.source_id,
  #  relationships.source_type,
  #  relationships.destination_id,
  #  relationships.destination_type,
  #  relationship_attrs.relationship_id,
  #  relationship_attrs.attr_value
  requests = defaultdict(str)
  for (reqid,
       relid, relctx, sid, stype, did, dtype,
       rattr_relid, rattr_value) in result:
    requests[reqid] += rattr_value

  return {k for k, v in requests.items() if attr_value not in v}


def get_request_person_key(stype, sid, did):
  """Returns ordered Request-Person key."""
  if stype == "Request":
    return "{}-{}".format(sid, did)
  return "{}-{}".format(did, sid)


def get_attr_values_for_processed_requests(connection, requests):
  """Get existing relationship attributes for requests - persons mappings. We
  need this to ensure that we don't overwrite/remove any existing roles.
  E.g. if request that is verified has requester and assignee specified but not
  verifier and one of the auditors is already assignee we must keep assignee
  role as well.

  It returns a dictionary with RequestID-PersonID keys and a list of current
  roles.
  """

  s = select([requests_table.c.id,
              relationships_table.c.id,
              relationships_table.c.source_type,
              relationships_table.c.source_id,
              relationships_table.c.destination_type,
              relationships_table.c.destination_id,
              relationship_attrs_table.c.attr_value
              ]).select_from(
      requests_table.join(
          relationships_table, or_(and_(
              relationships_table.c.source_type == "Request",
              relationships_table.c.source_id == requests_table.c.id,
              relationships_table.c.destination_type == "Person"
          ),
              and_(
              relationships_table.c.destination_type == "Request",
              relationships_table.c.destination_id == requests_table.c.id,
              relationships_table.c.source_type == "Person"
          )
          )
      ).join(
          relationship_attrs_table,
          relationship_attrs_table.c.relationship_id ==
          relationships_table.c.id)).where(
      requests_table.c.id.in_(list(requests)))
  result = connection.execute(s).fetchall()

  person_attr = dict()
  for reqid, relid, stype, sid, dtype, did, value in result:
    key = get_request_person_key(stype, sid, did)
    person_attr[key] = (relid, value.split(","))
  return person_attr


def add_request_person_mappings(existing_person_attr_values, req, ctx, pid,
                                roles):
  key = get_request_person_key("Request", req, pid)
  relid = None
  if key in existing_person_attr_values:
    relid, er = existing_person_attr_values[key]
    existing_roles = set(er)
    new_roles = set(roles)
    roles = list(existing_roles | new_roles)
  return relid, (req, ctx, pid, roles)


def get_program_audit_contexts(connection):
  """For every request returns its audits context and context from program
  that audit is belonging to."""
  s = select([
      requests_table.c.id,
      audits_table.c.context_id,
      audits_table.c.contact_id,
      programs_table.c.context_id,
  ]).select_from(
      requests_table
      .join(audits_table,
            requests_table.c.audit_id == audits_table.c.id)
      .join(programs_table,
            programs_table.c.id == audits_table.c.program_id
            )).where(
      requests_table.c.status.in_(["Final", "Verified"]))
  return connection.execute(s).fetchall()


def upgrade():
  connection = op.get_bind()

  # Gather data for processing
  # Requests that we can touch (only Final and Verified)
  verified_requests = get_requests_for_processing(connection, "Verified")
  final_requests = get_requests_for_processing(connection, "Final")
  requests = verified_requests | final_requests

  # Get contexts for auditors and program owners
  audits_contexts = get_auditors_contexts(connection)
  programs_contexts = get_programowners_contexts(connection)

  # Get requests that are missing requesters and verifiers
  missing_requesters = get_requests_with_no_attr(connection, "Requester")
  missing_verifiers = get_requests_with_no_attr(connection, "Verifier")

  # Get existing request to person mappings with associated current attribute
  # values. This is needed in case a person is already an assignee/requester
  # somewhere and only needs one new role.
  # It returns a dictionary with RequestID-PersonID keys and
  existing_person_attr_values = \
      get_attr_values_for_processed_requests(connection, requests)

  # Get contexts from audits and programs
  request_audit_program_contexts = get_program_audit_contexts(connection)

  # Make auditor(s), internal audit leads or program owner(s) Requesters and/or
  # Verifiers. For Final request we only need to attach a Requester role to the
  # Request, for Verified we also need to add Verifiers.

  # Before creating new relationships and relationship attributes we first
  # delete old relationships and associated relationship attributes.
  # We use this instead of update to enable batch operation and simplify code
  relationships_for_deletion = []

  # Build new Request - Person mappings with associated roles on the following
  # logic:
  # 1. We only attach Verifiers to Verified Requests
  # 2. We never forget existing role
  # 3. If something is missing, all person(s) will get new roles (all auditors
  #   or all program owners)
  # 4. We look for persons in the following order:
  #   4.1 Auditors from Request's Audit
  #   4.2 Audit's Internal Audit Lead
  #   4.3 Audit's Program's Program Owners
  request_person_mappings = []
  for req, actx, alid, pctx in request_audit_program_contexts:
    role = []
    # Only attach requester if none is present at the moment
    if req in missing_requesters:
      role += ["Requester"]

    # Only attach verifier if none is present at the moment
    # Only add verifier roles if request is verified
    if req in missing_verifiers and req in verified_requests:
      role += ["Verifier"]

    # First, try to get auditors, if that fails use internal audit lead and if
    # even that is not present, use program owners.
    if actx in audits_contexts:
      for p in audits_contexts[actx]:
        relid, mapping = add_request_person_mappings(
            existing_person_attr_values, req, actx, p, role)
        request_person_mappings += [mapping]
        relationships_for_deletion += [relid]
    elif alid:
      relid, mapping = add_request_person_mappings(
          existing_person_attr_values, req, actx, alid, role)
      request_person_mappings += [mapping]
      relationships_for_deletion += [relid]
    elif pctx in programs_contexts:
      for p in programs_contexts[pctx]:
        # We want to attach audit context, not program's context
        relid, mapping = add_request_person_mappings(
            existing_person_attr_values, req, actx, p, role)
        request_person_mappings += [mapping]
        relationships_for_deletion += [relid]

  relationship_id = _get_max_relationship_id(connection)

  relationships = []
  relationship_attrs = []
  for req, ctx, pid, attr_value in request_person_mappings:
    relationship_id += 1
    relationships += [
        build_bulk_insert_people_object(relationship_id, ctx, req, pid)]
    relationship_attrs += [
        build_bulk_insert_rel_attr_object(relationship_id, attr_value)
    ]

  # Delete old relationship attributes
  connection.execute(
      relationship_attrs_table.delete().where(
          relationship_attrs_table.c.relationship_id.in_(
              filter(lambda x: x, relationships_for_deletion))))

  # Delete deprecated relationships that will get replaced with new ones on
  # bulk insert
  connection.execute(
      relationships_table.delete().where(
          relationships_table.c.id.in_(
              filter(lambda x: x, relationships_for_deletion))
      )
  )

  # Bulk insert relationships and relationship attributes
  op.bulk_insert(relationships_table, relationships)
  op.bulk_insert(relationship_attrs_table, relationship_attrs)


def downgrade():
  pass
