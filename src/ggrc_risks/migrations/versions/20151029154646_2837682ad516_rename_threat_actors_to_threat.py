# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: anze@reciprocitylabs.com
# Maintained By: anze@reciprocitylabs.com

"""Rename threat actors to threat

Revision ID: 2837682ad516
Revises: 39518b8ea21d
Create Date: 2015-10-29 15:46:46.294919

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '2837682ad516'
down_revision = '39518b8ea21d'


def upgrade():
  op.execute("RENAME TABLE threat_actors TO threats")


def downgrade():
  op.execute("RENAME TABLE threats TO threat_actors")
