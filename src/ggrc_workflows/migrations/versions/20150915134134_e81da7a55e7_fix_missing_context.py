# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: anze@reciprocitylabs.com
# Maintained By: anze@reciprocitylabs.com


"""Fix missing context

Revision ID: e81da7a55e7
Revises: 1a4241cfd4cd
Create Date: 2015-09-15 13:41:34.878664

"""

# revision identifiers, used by Alembic.
revision = 'e81da7a55e7'
down_revision = '1a4241cfd4cd'

from alembic import op


def upgrade():
  op.execute("""
      UPDATE task_groups
      SET context_id =
          (SELECT context_id FROM workflows WHERE id = workflow_id)
      WHERE context_id is NULL;
  """)

  op.execute("""
      UPDATE task_group_tasks
      SET context_id =
          (SELECT context_id FROM task_groups WHERE id = task_group_id)
      WHERE context_id is NULL;
  """)

  op.execute("""
      UPDATE task_group_objects
      SET context_id =
          (SELECT context_id FROM task_groups WHERE id = task_group_id)
      WHERE context_id is NULL;
  """)


def downgrade():
  pass
