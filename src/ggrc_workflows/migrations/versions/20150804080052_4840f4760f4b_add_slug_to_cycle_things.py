# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com


"""Add slug to CycleThings

Revision ID: 4840f4760f4b
Revises: 3605dca868e4
Create Date: 2015-08-04 08:00:52.606565

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4840f4760f4b'
down_revision = '3605dca868e4'


_tables_prefixes = [
    ("cycle_task_groups", "CYCLEGROUP-"),
    ("cycle_task_group_object_tasks", "CYCLETASK-"),
]
_column_name = "slug"
_constraint_name = "unique_{}".format(_column_name)


def upgrade():
  """ Add and fill a unique slug column """
  for _table_name, _slug_prefix in _tables_prefixes:
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
  for _table_name, _slug_prefix in _tables_prefixes:
    op.drop_constraint(_constraint_name, _table_name, type_="unique")
    op.drop_column(_table_name, _column_name)
