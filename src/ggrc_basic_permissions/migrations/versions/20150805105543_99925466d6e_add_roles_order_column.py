# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

"""Add roles order column

Revision ID: 99925466d6e
Revises: 401fb7f0184b
Create Date: 2015-08-05 10:55:43.992382

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '99925466d6e'
down_revision = '401fb7f0184b'


def upgrade():
  op.add_column("roles", sa.Column("role_order", sa.Integer(), nullable=True))
  op.execute("UPDATE roles SET role_order = id")

  # creator role should appear before other roles
  op.execute("UPDATE roles SET role_order = 4 WHERE name='Creator'")


def downgrade():
  op.drop_column("roles", "role_order")
