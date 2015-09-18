# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com


"""add slug to task group task

Revision ID: 3605dca868e4
Revises: 1431e7094e26
Create Date: 2015-07-14 22:06:05.063945

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3605dca868e4"
down_revision = "1431e7094e26"


_table_name = "task_group_tasks"
_column_name = "slug"
_slug_prefix = "TASK-"
_constraint_name = "unique_{}".format(_column_name)


def upgrade():
  """ Add and fill a unique slug column """
  op.add_column(
      _table_name,
      sa.Column(_column_name, sa.String(length=250), nullable=True)
  )

  op.execute("UPDATE {table_name} SET slug = CONCAT('{prefix}', id)".format(
      table_name=_table_name,
      prefix=_slug_prefix
  ))

  op.alter_column(
      _table_name,
      _column_name,
      existing_type=sa.String(length=250),
      nullable=False
  )

  op.create_unique_constraint(_constraint_name, _table_name, [_column_name])


def downgrade():
  """ Remove slug column from task group tasks """
  op.drop_constraint(_constraint_name, _table_name, type_="unique")
  op.drop_column(_table_name, _column_name)
