
"""Disable task assignee nullification

Revision ID: 17f4ddff502e
Revises: 2b89912f95f1
Create Date: 2015-05-13 06:16:34.895339

"""

# revision identifiers, used by Alembic.
revision = '17f4ddff502e'
down_revision = '2b89912f95f1'

from alembic import op
import sqlalchemy as sa

tables = ["cycle_task_group_object_tasks", "cycle_task_group_objects",
          "cycle_task_groups", "task_group_tasks", "task_groups"]

def get_first_admin():
    conn = op.get_bind()

    res = conn.execute("""
    SELECT id FROM people
    WHERE email="prasannav@google.com"
    ORDER BY created_at ASC
    LIMIT 1
    """)
    prasanna = res.fetchall()

    if len(prasanna):
        return prasanna[0][0]

    res = conn.execute("""
    SELECT person_id FROM user_roles
    WHERE role_id=(SELECT id FROM roles
                   WHERE name="Superuser")
    ORDER BY created_at  ASC
    LIMIT 1
    """)
    superuser = res.fetchall()

    if len(superuser):
        return superuser[0][0]


    res = conn.execute("""
    SELECT person_id FROM user_roles
    WHERE role_id=(SELECT id FROM roles
                   WHERE name="gGRC Admin")
    ORDER BY created_at  ASC
    LIMIT 1
    """)
    admin = res.fetchall()

    if len(admin):
        return admin[0][0]

    raise LookupError("Can't find default admin user")

def upgrade():
    first_admin_id = get_first_admin()

    for table in tables:
        op.execute("""
        UPDATE %s
        SET contact_id=%d
        WHERE contact_id IS NULL;
        """ % (table, first_admin_id))

        op.execute("""
        ALTER TABLE %s MODIFY contact_id int(11) NOT NULL
        """ % table)


def downgrade():
    for table in tables:
        op.execute("""
        ALTER TABLE %s MODIFY contact_id int(11);
        """ % table)
