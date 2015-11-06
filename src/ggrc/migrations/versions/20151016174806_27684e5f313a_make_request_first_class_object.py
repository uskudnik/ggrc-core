
"""Make Request First-class object

Revision ID: 27684e5f313a
Revises: 3c8f204ba7a9
Create Date: 2015-10-16 17:48:06.875436

"""

# revision identifiers, used by Alembic.
revision = '27684e5f313a'
down_revision = '45693b1959f7'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from HTMLParser import HTMLParser
import bleach

from ggrc import db
from ggrc.models import Request


def cleaner(value, bleach_tags=[], bleach_attrs={}):
  if value is None:
    return value

  parser = HTMLParser()
  lastvalue = value
  value = parser.unescape(value)
  while value != lastvalue:
    lastvalue = value
    value = parser.unescape(value)

  ret = parser.unescape(
    bleach.clean(value, bleach_tags, bleach_attrs, strip=True)
  )
  return ret


def upgrade():
    sql = "BEGIN;"
    # 1. Move Audit Objects to Relationship table
    #   source_type = audit_objects.auditable_type
    #   source_id = audit_objects.auditable_id
    #   destination_type = "Request"
    #   destination_id = request.id
    sql += """
    INSERT INTO relationships (
      modified_by_id,
      created_at,
      updated_at,
      source_id,
      source_type,
      destination_id,
      destination_type,
      context_id) SELECT
        AO.modified_by_id,
        NOW(),
        NOW(),
        AO.auditable_id,
        AO.auditable_type,
        R.id,
        "Request",
        AO.context_id
      FROM requests AS R, audit_objects AS AO WHERE AO.id = R.audit_object_id;
    """
    # 2. Create relations to Audits in Relationship table
    #   source_type = Audit
    #   source_id   = audit.id
    #   destionation_type = Request
    #   destination_id = request.id
    sql += """
    INSERT INTO relationships (
      modified_by_id,
      created_at,
      updated_at,
      source_id,
      source_type,
      destination_id,
      destination_type,
      context_id) SELECT
      AO.modified_by_id,
      NOW(),
      NOW(),
      AO.audit_id,
      "Audit",
      R.id,
      "Request",
      AO.context_id
      FROM requests AS R, audit_objects AS AO WHERE AO.id = R.audit_object_id;
    """

    # 3. Change status values
    sql += """
    ALTER TABLE requests CHANGE status status ENUM('Draft','Requested','Responded','Amended Request','Updated Response','Accepted','Unstarted','In Progress','Finished','Verified') NOT NULL;

    UPDATE requests SET status='Unstarted' WHERE status='Draft';
    UPDATE requests SET status='In Progress' WHERE status='Requested';
    UPDATE requests SET status='Finished' WHERE status='Responded';
    UPDATE requests SET status='In Progress' WHERE status='Amended Request';
    UPDATE requests SET status='Finished' WHERE status='Updated Response';
    UPDATE requests SET status='Verified' WHERE status='Accepted';

    ALTER TABLE requests CHANGE status status ENUM('Unstarted','In Progress','Finished','Verified') NOT NULL;
    """

    # Move assignees into relationships
    sql += """
    INSERT INTO relationships (
      modified_by_id,
      created_at,
      updated_at,
      source_type,
      source_id,
      destination_type,
      destination_id
    ) SELECT
      modified_by_id,
      created_at,
      updated_at,
      "Request",
      id,
      "Person",
      assignee_id
    FROM requests;

    INSERT INTO relationship_attrs (
      relationship_id,
      attr_name,
      attr_value
    ) SELECT
      relationships.id, "AssigneeType", "Assignee"
      FROM requests
      JOIN relationships ON (relationships.source_id = requests.id)
      WHERE relationships.source_type = "Request";

    ALTER TABLE requests DROP FOREIGN KEY requests_ibfk_1;
    ALTER TABLE requests MODIFY COLUMN assignee_id INT(11) NULL;
    """

    sql += "COMMIT;"
    op.execute(sql)

    requests = db.session.query(Request)
    for request in requests:
        cleaned_desc = cleaner(request.description)
        request.title = cleaned_desc[:60]
        db.session.add(request)
    db.session.commit()

    # Remove unneeded attributes
    # sql = "BEGIN;"
    # # 3. Drop FK audit_objects_id from Request
    # sql += """
    # ALTER TABLE requests DROP FOREIGN KEY requests_audit_objects_ibfk;
    # DROP INDEX requests_audit_objects_ibfk ON requests;
    # ALTER TABLE requests DROP COLUMN audit_object_id;
    # """
    # # 4. Drop audit_id from Request
    # sql += """
    # ALTER TABLE requests DROP FOREIGN KEY requests_ibfk_2;
    # ALTER TABLE requests DROP COLUMN audit_id;
    # """
    # sql += "COMMIT;"
    # op.execute(sql)


    # TODO: drop requests table from audits

    # TODO: 5. Link all objects that are mapped to Audit to requests

    # TODO: Drop relationship audit_objects from Audits????


def downgrade():
    pass
