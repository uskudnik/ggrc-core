# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: swizec@reciprocitylabs.com
# Maintained By: swizec@reciprocitylabs.com

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

from ggrc_workflows.models.task_group_task import TaskGroupTask
from ggrc_workflows.models.task_group import TaskGroup
from ggrc_workflows.models.cycle_task_group import CycleTaskGroup
from ggrc_workflows.models.cycle_task_group_object import CycleTaskGroupObject
from ggrc_workflows.models.cycle_task_group_object_task import CycleTaskGroupObjectTask
from ggrc_basic_permissions.models import Role, UserRole
from ggrc.models.person import Person

models = [CycleTaskGroupObjectTask, CycleTaskGroupObject, CycleTaskGroup, TaskGroupTask, TaskGroup]

def get_first_admin():
    prasanna = Person.query.filter(sa.and_(Person.email == "prasannav@google.com",
                                           Person.is_enabled == True)).first()

    if prasanna:
        return prasanna.id

    superuser = UserRole.query.filter(
            UserRole.role == Role.query.filter(Role.name == "Superuser").first()
        ).first()

    if superuser:
        return superuser.person.id

    admin = UserRole.query.filter(
        UserRole.role == Role.query.filter(Role.name == "gGRC Admin").first()
    ).first()

    if admin:
        return admin.person.id

    raise LookupError("Can't find default admin user")


def upgrade():
    if any(model.query.filter(model.contact_id == None).count()
           for model in models):

        first_admin_id = get_first_admin()

        for model in models:
            op.execute(model.__table__.update()\
              .where(model.contact_id == None)\
              .values({"contact_id": first_admin_id})
            )

    for model in models:
        op.execute("""
        ALTER TABLE %s MODIFY contact_id int(11) NOT NULL
        """ % model.__tablename__)

def downgrade():
    for model in models:
        op.execute("""
        ALTER TABLE %s MODIFY contact_id int(11);
        """ % model.__tablename__)
