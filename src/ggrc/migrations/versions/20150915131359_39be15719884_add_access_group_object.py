# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

"""Add Access Group object

Revision ID: 39be15719884
Revises: 2d8a46b1e4a4
Create Date: 2015-09-15 13:13:59.320295

"""

# revision identifiers, used by Alembic.
revision = '39be15719884'
down_revision = '29dca3ce0556'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.create_table('access_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('os_state', sa.String(length=250), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=250), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('url', sa.String(length=250), nullable=True),
    sa.Column('reference_url', sa.String(length=250), nullable=True),
    sa.Column('secondary_contact_id', sa.Integer(), nullable=True),
    sa.Column('contact_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=250), nullable=False),
    sa.Column('slug', sa.String(length=250), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('modified_by_id', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('context_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['contact_id'], ['people.id'], ),
    sa.ForeignKeyConstraint(['context_id'], ['contexts.id'], ),
    sa.ForeignKeyConstraint(['secondary_contact_id'], ['people.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug', name='uq_access_groups'),
    sa.UniqueConstraint('title', name='uq_t_access_groups')
    )
    op.create_index('fk_access_groups_contact', 'access_groups', ['contact_id'], unique=False)
    op.create_index('fk_access_groups_contexts', 'access_groups', ['context_id'], unique=False)
    op.create_index('fk_access_groups_secondary_contact', 'access_groups', ['secondary_contact_id'], unique=False)
    op.create_index('ix_access_groups_updated_at', 'access_groups', ['updated_at'], unique=False)



def downgrade():
    op.drop_index('ix_access_groups_updated_at', table_name='access_groups')
    op.drop_index('fk_access_groups_secondary_contact', table_name='access_groups')
    op.drop_index('fk_access_groups_contexts', table_name='access_groups')
    op.drop_index('fk_access_groups_contact', table_name='access_groups')
    op.drop_table('access_groups')
