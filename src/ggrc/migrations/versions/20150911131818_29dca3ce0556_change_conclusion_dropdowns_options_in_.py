# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: jost@reciprocitylabs.com
# Maintained By: jost@reciprocitylabs.com

"""Change conclusion dropdowns options in control assessment

Revision ID: 29dca3ce0556
Revises: 2d8a46b1e4a4
Create Date: 2015-09-11 13:18:18.269109

"""

# revision identifiers, used by Alembic.
revision = '29dca3ce0556'
down_revision = '2d8a46b1e4a4'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    sql = """
    UPDATE control_assessments
    SET design = 'Ineffective'
    WHERE
        design = 'Material weakness' OR
        design = 'Significant deficiency'
    """
    op.execute(sql)

    sql = """
    UPDATE control_assessments
    SET operationally = 'Ineffective'
    WHERE
        operationally = 'Material weakness' OR
        operationally = 'Significant deficiency'
    """
    op.execute(sql)


def downgrade():
    sql = """
    UPDATE control_assessments
    SET design = 'Significant deficiency'
    WHERE design = 'Ineffective'
    """
    op.execute(sql)

    sql = """
    UPDATE control_assessments
    SET operationally = 'Significant deficiency'
    WHERE operationally = 'Ineffective'
    """
    op.execute(sql)
