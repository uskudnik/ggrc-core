# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Add Snapshot model

Create Date: 2016-07-28 14:09:21.338385
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2a5a39600741"
down_revision = "1db61b597d2d"


def upgrade():
  """Add snapshots table"""
  op.create_table(
      "snapshots",
      sa.Column("id", sa.Integer(), nullable=False),

      sa.Column("parent_id", sa.Integer(), nullable=False),
      sa.Column("parent_type", sa.String(length=250), nullable=False),

      sa.Column("child_id", sa.Integer(), nullable=False),
      sa.Column("child_type", sa.String(length=250), nullable=False),

      sa.Column("revision_id", sa.Integer(), nullable=False),

      sa.Column("context_id", sa.Integer(), nullable=True),

      sa.Column("created_at", sa.DateTime(), nullable=False),
      sa.Column("updated_at", sa.DateTime(), nullable=False),
      sa.Column("modified_by_id", sa.Integer(), nullable=False),

      sa.PrimaryKeyConstraint("id"),
      sa.ForeignKeyConstraint(["revision_id"], ["revisions.id"])
  )

  op.create_index("ix_snapshots_parent", "snapshots",
                  ["parent_type", "parent_id"],
                  unique=False)
  op.create_index("ix_snapshots_child", "snapshots",
                  ["child_type", "child_id"],
                  unique=False)

  # Feature flag for audits that had snapshoted objects instead of mapped
  # objects
  op.add_column("audits",
                sa.Column("ff_snapshot_enabled",
                          sa.Boolean(), default=False, nullable=True))


def downgrade():
  """Drop snapshots table and audit's FF for snapshots"""
  op.drop_table("snapshots")
  op.drop_column("audits", "ff_snapshot_enabled")
