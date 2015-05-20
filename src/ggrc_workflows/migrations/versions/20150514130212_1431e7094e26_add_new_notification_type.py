
"""add new notification type

Revision ID: 1431e7094e26
Revises: 2b89912f95f1
Create Date: 2015-05-14 13:02:12.165612

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import timedelta, date
from sqlalchemy import and_
from ggrc import db
from ggrc_workflows.models import Workflow
from ggrc_workflows.notification.notification_handler import (
    get_notification_type,
    add_notif,
)

# revision identifiers, used by Alembic.
revision = '1431e7094e26'
down_revision = '2b89912f95f1'


def upgrade():
  notification_types_table = table(
      'notification_types',
      column('id', sa.Integer),
      column('name', sa.String),
      column('description', sa.Text),
      column('template', sa.String),
      column('instant', sa.Boolean),
      column('advance_notice', sa.Integer),
      column('advance_notice_end', sa.Integer),
      column('created_at', sa.DateTime),
      column('modified_by_id', sa.Integer),
      column('updated_at', sa.DateTime),
      column('context_id', sa.Integer),
  )

  notification_types = [
      # cycle created notifictions
      {"name": "cycle_start_failed",
       "description": ("Notify workflow owners that a cycle has failed to"
                       "start for a recurring workflow"),
       "template": "cycle_start_failed",
       "advance_notice": 0,
       "instant": False,
       },
  ]

  op.bulk_insert(notification_types_table, notification_types)

  existing_wfs = Workflow.query.filter(and_(
      Workflow.frequency.in_(["weekly", "monthly", "quarterly", "annually"]),
      Workflow.next_cycle_start_date >= date.today()
  ))
  for wf in existing_wfs:
    notif_type = get_notification_type("cycle_start_failed")
    add_notif(wf, notif_type, wf.next_cycle_start_date + timedelta(1))

  db.session.commit()


def downgrade():
  pass
