# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com


"""Make task_group_id nullable

Revision ID: 1a4241cfd4cd
Revises: 44047daa31a9
Create Date: 2015-08-12 10:48:03.112117

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1a4241cfd4cd'
down_revision = '44047daa31a9'


def upgrade():
  op.alter_column(
      "cycle_task_groups",
      "task_group_id",
      existing_type=sa.Integer(),
      nullable=True
  )


def downgrade():
  op.alter_column(
      "cycle_task_groups",
      "task_group_id",
      existing_type=sa.Integer(),
      nullable=False
  )
