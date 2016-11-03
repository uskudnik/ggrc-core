# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Audit model."""

from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.mixins import (
    Timeboxed, Noted, Described, Hyperlinked, WithContact,
    Titled, Slugged, CustomAttributable
)
from ggrc.utils import benchmark

from ggrc.models.mixins import clonable
from ggrc.models.relationship import Relatable
from ggrc.models.object_person import Personable
from ggrc.models.context import HasOwnContext
from ggrc.models.reflection import AttributeInfo
from ggrc.models.reflection import PublishOnly
from ggrc.models.program import Program
from ggrc.models.person import Person

from ggrc.models.snapshot import Snapshotable


class Audit(Snapshotable, clonable.Clonable,
            CustomAttributable, Personable, HasOwnContext, Relatable,
            Timeboxed, Noted, Described, Hyperlinked, WithContact, Titled,
            Slugged, db.Model):
  """Audit model."""

  __tablename__ = 'audits'
  _slug_uniqueness = False

  VALID_STATES = (
      u'Planned', u'In Progress', u'Manager Review',
      u'Ready for External Review', u'Completed'
  )

  CLONEABLE_CHILDREN = {"AssessmentTemplate"}

  report_start_date = deferred(db.Column(db.Date), 'Audit')
  report_end_date = deferred(db.Column(db.Date), 'Audit')
  audit_firm_id = deferred(
      db.Column(db.Integer, db.ForeignKey('org_groups.id')), 'Audit')
  audit_firm = db.relationship('OrgGroup', uselist=False)
  # TODO: this should be stateful mixin
  status = deferred(db.Column(db.Enum(*VALID_STATES), nullable=False),
                    'Audit')
  gdrive_evidence_folder = deferred(db.Column(db.String), 'Audit')
  program_id = deferred(
      db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False),
      'Audit')
  requests = db.relationship(
      'Request', backref='audit', cascade='all, delete-orphan')
  audit_objects = db.relationship(
      'AuditObject', backref='audit', cascade='all, delete-orphan')
  object_type = db.Column(
      db.String(length=250), nullable=False, default='Control')

  # Feature flag for audits that had snapshoted objects instead of mapped
  # objects
  ff_snapshot_enabled = db.Column(
      db.Boolean(), nullable=True, default=False
  )

  _publish_attrs = [
      "ff_snapshot_enabled",
      "report_start_date",
      "report_end_date",
      "audit_firm",
      "status",
      "gdrive_evidence_folder",
      "program",
      "requests",
      "object_type",
      PublishOnly("audit_objects")
  ]

  _sanitize_html = [
      'gdrive_evidence_folder',
      'description',
  ]

  _include_links = []

  _aliases = {
      "program": {
          "display_name": "Program",
          "filter_by": "_filter_by_program",
          "mandatory": True,
      },
      "user_role:Auditor": {
          "display_name": "Auditors",
          "type": AttributeInfo.Type.USER_ROLE,
          "filter_by": "_filter_by_auditor",
      },
      "status": "Status",
      "start_date": "Planned Start Date",
      "end_date": "Planned End Date",
      "report_start_date": "Planned Report Period from",
      "report_end_date": "Planned Report Period to",
      "contact": {
          "display_name": "Internal Audit Lead",
          "mandatory": True,
          "filter_by": "_filter_by_contact",
      },
      "secondary_contact": None,
      "notes": None,
      "url": None,
      "reference_url": None,
  }

  def _clone(self, source_object):
    """Clone audit and all relevant attributes.

    Keeps the internals of actual audit cloning and everything that is related
    to audit itself (auditors, audit firm, context setting,
    custom attribute values, etc.)
    """
    from ggrc_basic_permissions import create_audit_context
    from ggrc.snapshotter import SnapshotGenerator
    from ggrc.models import Snapshot
    from ggrc.snapshotter.datastructures import Pair
    from ggrc.snapshotter.datastructures import Stub
    from ggrc.snapshotter.helpers import get_event

    data = {
        "title": source_object.generate_attribute("title"),
        "description": source_object.description,
        "audit_firm": source_object.audit_firm,
        "start_date": source_object.start_date,
        "end_date": source_object.end_date,
        "program": source_object.program,
        "status": source_object.VALID_STATES[0],
        "report_start_date": source_object.report_start_date,
        "report_end_date": source_object.report_end_date,
        "contact": source_object.contact
    }

    self.update_attrs(data)
    db.session.flush()

    create_audit_context(self)
    self._clone_auditors(source_object)
    self.clone_custom_attribute_values(source_object)

    with benchmark("audit.py:Audit._clone.clone audit scope"):
      source_snapshot = db.session.query(
          Snapshot.child_type,
          Snapshot.child_id,
          Snapshot.revision_id
      ).filter(
          Snapshot.parent_type == source_object.type,
          Snapshot.parent_id == source_object.id
      )
      snapshot_revisions = {
          Pair.from_4tuple((self.type, self.id, ctype, cid)):
          revid
          for ctype, cid, revid in source_snapshot}

      event = get_event(self, "POST")
      parent = Stub(self.type, self.id)
      children = {pair.child for pair in snapshot_revisions}
      generator = SnapshotGenerator(dry_run=False)
      generator.add_family(parent, children)
      generator.create(event, snapshot_revisions)

  def _clone_auditors(self, audit):
    """Clone auditors of specified audit.

    Args:
      audit: Audit instance
    """
    from ggrc_basic_permissions.models import Role, UserRole

    role = Role.query.filter_by(name="Auditor").first()
    auditors = [ur.person for ur in UserRole.query.filter_by(
        role=role, context=audit.context).all()]

    for auditor in auditors:
      user_role = UserRole(
          context=self.context,
          person=auditor,
          role=role
      )
      db.session.add(user_role)
    db.session.flush()

  def clone(self, source_id, mapped_objects=None):
    """Clone audit with specified whitelisted children.

    Children that can be cloned should be specified in CLONEABLE_CHILDREN.

    Args:
      mapped_objects: A list of related objects that should also be copied and
      linked to a new audit.
    """
    if not mapped_objects:
      mapped_objects = []

    source_object = Audit.query.get(source_id)
    self._clone(source_object)

    if any(mapped_objects):
      related_children = source_object.related_objects(mapped_objects)

      for obj in related_children:
        obj.clone(self)

  @classmethod
  def _filter_by_program(cls, predicate):
    return Program.query.filter(
        (Program.id == Audit.program_id) &
        (predicate(Program.slug) | predicate(Program.title))
    ).exists()

  @classmethod
  def _filter_by_auditor(cls, predicate):
    from ggrc_basic_permissions.models import Role, UserRole
    return UserRole.query.join(Role, Person).filter(
        (Role.name == "Auditor") &
        (UserRole.context_id == cls.context_id) &
        (predicate(Person.name) | predicate(Person.email))
    ).exists()

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Audit, cls).eager_query()
    return query.options(
        orm.joinedload('program'),
        orm.subqueryload('requests'),
        orm.subqueryload('object_people').joinedload('person'),
        orm.subqueryload('audit_objects'),
    )
