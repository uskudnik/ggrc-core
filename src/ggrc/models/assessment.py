# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: anze@reciprocitylabs.com
# Maintained By: anze@reciprocitylabs.com

from sqlalchemy.orm import validates

from ggrc import db
from ggrc.models import reflection
from ggrc.models.mixins_assignable import Assignable
from ggrc.models.mixin_autostatuschangable import AutoStatusChangable
from ggrc.models.mixins import BusinessObject
from ggrc.models.mixins import CustomAttributable
from ggrc.models.mixins import deferred
from ggrc.models.mixins import TestPlanned
from ggrc.models.mixins import Timeboxed
from ggrc.models.object_document import Documentable
from ggrc.models.object_owner import Ownable
from ggrc.models.object_person import Personable
from ggrc.models.reflection import PublishOnly
from ggrc.models.relationship import Relatable
from ggrc.models.track_object_state import HasObjectState
from ggrc.models.track_object_state import track_state_for_class


class Assessment(AutoStatusChangable, Assignable, HasObjectState, TestPlanned, CustomAttributable,
                 Documentable, Personable, Timeboxed, Ownable,
                 Relatable, BusinessObject, db.Model):
  __tablename__ = 'assessments'

  VALID_STATES = (u"Open", u"In Progress", u"Finished", u"Verified", u"Final")
  ASSIGNEE_TYPES = (u"Creator", u"Assessor", u"Verifier")

  status = deferred(db.Column(db.Enum(*VALID_STATES), nullable=False,
                    default=VALID_STATES[0]), "Assessment")

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
  }
  _tracked_date_attrs = {'start_date', 'end_date'}


  _aliases = {
      "audit": {
          "display_name": "Audit",
          "mandatory": True,
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
    return self.validate_conclusion(value)

  @validates("design")
  def validate_design(self, key, value):
    return self.validate_conclusion(value)

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
