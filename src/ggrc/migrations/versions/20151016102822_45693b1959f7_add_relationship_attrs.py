# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: andraz@reciprocitylabs.com
# Maintained By: andraz@reciprocitylabs.com

"""add relationship attrs

Revision ID: 45693b1959f7
Revises: 1ef8f4f504ae
Create Date: 2015-10-16 10:28:22.241136

"""

# revision identifiers, used by Alembic.
revision = '45693b1959f7'
down_revision = '3c8f204ba7a9'

from alembic import op
import sqlalchemy as sa


def upgrade():
  op.create_table(
      'relationship_attrs',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('relationship_id',  sa.Integer(), nullable=False),
      sa.Column('attr_name', sa.String(length=250), nullable=False),
      sa.Column('attr_value', sa.String(length=250), nullable=False),
      sa.PrimaryKeyConstraint('id'),
      sa.ForeignKeyConstraint(['relationship_id'], ['relationships.id'])
  )


def downgrade():
  op.drop_table('relationship_attrs')
