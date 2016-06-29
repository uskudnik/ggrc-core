# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for Assessment object"""

from sqlalchemy.orm import validates

from ggrc import db
from ggrc.models import mixins_reminderable
from ggrc.models import mixins_statusable
from ggrc.models import reflection
from ggrc.models.audit import Audit
from ggrc.models.comment import Commentable
from ggrc.models.mixin_autostatuschangable import AutoStatusChangable
from ggrc.models.mixins import CustomAttributable
from ggrc.models.mixins import Described
from ggrc.models.mixins import FinishedDate
from ggrc.models.mixins import Hyperlinked
from ggrc.models.mixins import Noted
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import TestPlanned
from ggrc.models.mixins import Timeboxed
from ggrc.models.mixins import Titled
from ggrc.models.mixins import VerifiedDate
from ggrc.models.mixins import WithContact
from ggrc.models.mixins import deferred
from ggrc.models.mixins_assignable import Assignable
from ggrc.models.object_document import Documentable
from ggrc.models.object_owner import Ownable
from ggrc.models.object_person import Personable
from ggrc.models.reflection import PublishOnly
from ggrc.models.relationship import Relatable
from ggrc.models.relationship import Relationship
from ggrc.models.track_object_state import HasObjectState
from ggrc.models.track_object_state import track_state_for_class


class Assessment(mixins_statusable.Statusable,
                 AutoStatusChangable, Assignable, HasObjectState, TestPlanned,
                 CustomAttributable, Documentable, Commentable, Personable,
                 mixins_reminderable.Reminderable, Timeboxed,
                 Ownable, Relatable, FinishedDate, VerifiedDate,
                 Noted, Described, Hyperlinked, WithContact,
                 Titled, Slugged, db.Model):
  """Class representing Assessment.

  Assessment is an object representing an individual assessment performed on
  a specific object during an audit to ascertain whether or not
  certain conditions were met for that object.
  """

  __tablename__ = 'assessments'
  _title_uniqueness = False

  ASSIGNEE_TYPES = (u"Creator", u"Assessor", u"Verifier")

  REMINDERABLE_HANDLERS = {
      "statusToPerson": {
          "handler":
              mixins_reminderable.Reminderable.handle_state_to_person_reminder,
          "data": {
              mixins_statusable.Statusable.START_STATE: "Assessor",
              "In Progress": "Assessor"
          },
          "reminders": {"assessment_assessor_reminder", }
      }
  }

  design = deferred(db.Column(db.String), "Assessment")
  operationally = deferred(db.Column(db.String), "Assessment")

  object = {}  # we add this for the sake of client side error checking
  audit = {}

  VALID_CONCLUSIONS = frozenset([
      "Effective",
      "Ineffective",
      "Needs improvement",
      "Not Applicable"
  ])

  # REST properties
  _publish_attrs = [
      'design',
      'operationally',
      PublishOnly('audit'),
      PublishOnly('object')
  ]

  _tracked_attrs = {
      'contact_id',
      'description',
      'design',
      'notes',
      'operationally',
      'reference_url',
      'secondary_contact_id',
      'test_plan',
      'title',
      'url',
      'start_date',
      'end_date'
  }

  _aliases = {
      "audit": {
          "display_name": "Audit",
          "mandatory": True,
          "filter_by": "_filter_by_audit",
      },
      "url": "Assessment URL",
      "design": "Conclusion: Design",
      "operationally": "Conclusion: Operation",
      "related_creators": {
          "display_name": "Creator",
          "mandatory": True,
          "filter_by": "_filter_by_related_creators",
          "type": reflection.AttributeInfo.Type.MAPPING,
      },
      "related_assessors": {
          "display_name": "Assessor",
          "mandatory": True,
          "filter_by": "_filter_by_related_assessors",
          "type": reflection.AttributeInfo.Type.MAPPING,
      },
      "related_verifiers": {
          "display_name": "Verifier",
          "filter_by": "_filter_by_related_verifiers",
          "type": reflection.AttributeInfo.Type.MAPPING,
      },
  }

  def validate_conclusion(self, value):
    return value if value in self.VALID_CONCLUSIONS else ""

  @validates("operationally")
  def validate_opperationally(self, key, value):
    # pylint: disable=unused-argument
    return self.validate_conclusion(value)

  @validates("design")
  def validate_design(self, key, value):
    # pylint: disable=unused-argument
    return self.validate_conclusion(value)

  @classmethod
  def _filter_by_audit(cls, predicate):
    return Relationship.query.filter(
        Relationship.source_type == cls.__name__,
        Relationship.source_id == cls.id,
        Relationship.destination_type == Audit.__name__,
    ).join(Audit, Relationship.destination_id == Audit.id).filter(
        predicate(Audit.slug)
    ).exists() | Relationship.query.filter(
        Relationship.destination_type == cls.__name__,
        Relationship.destination_id == cls.id,
        Relationship.source_type == Audit.__name__,
    ).join(Audit, Relationship.source_id == Audit.id).filter(
        predicate(Audit.slug)
    ).exists()

  @classmethod
  def _filter_by_related_creators(cls, predicate):
    return cls._get_relate_filter(predicate, "Creator")

  @classmethod
  def _filter_by_related_assessors(cls, predicate):
    return cls._get_relate_filter(predicate, "Assessor")

  @classmethod
  def _filter_by_related_verifiers(cls, predicate):
    return cls._get_relate_filter(predicate, "Verifier")

track_state_for_class(Assessment)
