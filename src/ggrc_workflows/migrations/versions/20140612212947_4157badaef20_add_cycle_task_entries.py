# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: anze@reciprocitylabs.com
# Maintained By: anze@reciprocitylabs.com


"""Add cycle_task_entries

Revision ID: 4157badaef20
Revises: 580d2ac5bc2d
Create Date: 2014-06-12 21:29:47.584269

"""

# revision identifiers, used by Alembic.
revision = '4157badaef20'
down_revision = '580d2ac5bc2d'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.create_table('cycle_task_entries',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('cycle_task_group_object_task_id', sa.Integer(), nullable=False),
      sa.Column('description', sa.Text(), nullable=True),
      sa.Column('created_at', sa.DateTime(), nullable=True),
      sa.Column('modified_by_id', sa.Integer(), nullable=True),
      sa.Column('updated_at', sa.DateTime(), nullable=True),
      sa.Column('context_id', sa.Integer(), nullable=True),
      sa.ForeignKeyConstraint(['context_id'], ['contexts.id'], ),
      sa.ForeignKeyConstraint(['cycle_task_group_object_task_id'], ['cycle_task_group_object_tasks.id'], ),
      sa.PrimaryKeyConstraint('id')
      )
    op.create_index('fk_cycle_task_entries_contexts', 'cycle_task_entries', ['context_id'], unique=False)

    op.drop_table('task_entries')


def downgrade():
    op.create_table('task_entries',
      sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
      sa.Column('description', mysql.TEXT(), nullable=True),
      sa.Column('created_at', mysql.DATETIME(), nullable=True),
      sa.Column('modified_by_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
      sa.Column('updated_at', mysql.DATETIME(), nullable=True),
      sa.Column('context_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
      sa.ForeignKeyConstraint(['context_id'], [u'contexts.id'], name=u'fk_task_entries_context_id'),
      sa.PrimaryKeyConstraint('id'),
      mysql_default_charset=u'utf8',
      mysql_engine=u'InnoDB'
      )

    #op.drop_index('fk_cycle_task_entries_contexts', table_name='cycle_task_entries')
    op.drop_table('cycle_task_entries')
