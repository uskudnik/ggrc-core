# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

"""Make NotificationConfig unique on per-type + per-person basis

Revision ID: 2d8a46b1e4a4
Revises: 49b2ecde7ad0
Create Date: 2015-09-08 17:56:00.151641

"""

# revision identifiers, used by Alembic.
from itertools import groupby

revision = '2d8a46b1e4a4'
down_revision = '3046ce611147'

from alembic import op

from ggrc import db
from ggrc.models import NotificationConfig

def upgrade():
    # This migration will delete all duplicate notification configurations on
    # per-notification type and per-person ID basis and add unique constraint
    # that should prevent future accidental duplication.

    notif_configs = db.session.query(
        NotificationConfig.id,
        NotificationConfig.notif_type,
        NotificationConfig.person_id,
        NotificationConfig.updated_at
    ).all()

    notif_types = {nc[1] for nc in notif_configs}
    to_delete = []
    for notif_type in notif_types:
        # Get all notifications of the same type and sort them by person_id
        notifs = filter(lambda x: x[1] == notif_type, notif_configs)
        notifs.sort(key=lambda x: x[2])
        # Group by person_id
        grouped = groupby(notifs, lambda x: x[2])
        # Expand the iterable to allow for count
        expanded = [(k, [x for x in g]) for k, g in grouped]
        # Get only duplicated configurations
        duplicated_user_config = filter(lambda x: len(x[1]) > 1, expanded)
        # Mark for deletion all configs BUT the last one that was modified
        for pid, duc in duplicated_user_config:
            duc = sorted(duc, key=lambda x: x[3], reverse=True)
            to_delete += [str(cid) for cid, t, pid, u in duc[1:]]
    db.session.close()

    if to_delete:
        sql = "DELETE FROM notification_configs WHERE id IN ({});".format(
            ", ".join(to_delete))
        op.execute(sql)

    op.create_unique_constraint("uq_notif_configs_person_id_notif_type",
                                "notification_configs",
                                ["person_id", "notif_type"])


def downgrade():
    op.drop_constraint(
        "uq_notif_configs_person_id_notif_type", "notification_configs")
