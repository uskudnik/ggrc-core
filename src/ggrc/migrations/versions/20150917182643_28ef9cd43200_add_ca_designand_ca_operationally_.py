# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

"""Add CA.design and CA.operationally columns to options table

Revision ID: 28ef9cd43200
Revises: 2d8a46b1e4a4
Create Date: 2015-09-17 18:26:43.829846

"""

# revision identifiers, used by Alembic.
revision = '28ef9cd43200'
down_revision = '2d8a46b1e4a4'

from alembic import op


def upgrade():
    op.execute("""INSERT INTO options (created_at, updated_at, role, title) VALUES
      (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'control_assessment_design', 'Effective'),
      (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'control_assessment_design', 'Material weakness'),
      (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'control_assessment_design', 'Needs improvement'),
      (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'control_assessment_design', 'Significant deficiency'),
      (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'control_assessment_design', 'Not Applicable'),
      (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'control_assessment_operationally', 'Effective'),
      (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'control_assessment_operationally', 'Material weakness'),
      (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'control_assessment_operationally', 'Needs improvement'),
      (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'control_assessment_operationally', 'Significant deficiency'),
      (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'control_assessment_operationally', 'Not Applicable');
    """)


def downgrade():
    pass