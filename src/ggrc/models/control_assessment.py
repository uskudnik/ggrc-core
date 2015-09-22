# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: anze@reciprocitylabs.com
# Maintained By: anze@reciprocitylabs.com

from sqlalchemy import orm
from sqlalchemy.orm import validates
from uuid import uuid1

from ggrc import db
from ggrc.models.mixins import BusinessObject
from ggrc.models.mixins import CustomAttributable
from ggrc.models.mixins import TestPlanned
from ggrc.models.mixins import Timeboxed
from ggrc.models.mixins import deferred
from ggrc.models.control import Control
from ggrc.models.object_document import Documentable
from ggrc.models.object_owner import Ownable
from ggrc.models.object_person import Personable
from ggrc.models.reflection import PublishOnly
from ggrc.models.relationship import Relatable
from ggrc.models.track_object_state import HasObjectState
from ggrc.models.track_object_state import track_state_for_class


class ControlAssessment(HasObjectState, TestPlanned, CustomAttributable,
                        Documentable, Personable, Timeboxed, Ownable,
                        Relatable, BusinessObject, db.Model):
  __tablename__ = 'control_assessments'

  design = deferred(db.Column(db.String), 'ControlAssessment')
  operationally = deferred(db.Column(db.String), 'ControlAssessment')

  control_id = db.Column(db.Integer, db.ForeignKey('controls.id'))
  control = db.relationship('Control', foreign_keys=[control_id])

  audit = {}  # we add this for the sake of client side error checking

  VALID_CONCLUSIONS = frozenset([
      "Effective", "Ineffective", "Needs improvement",
      "Not Applicable"
  ])

  # REST properties
  _publish_attrs = [
      'design',
      'operationally',
      'control',
      PublishOnly('audit')
  ]

  _aliases = {
      "control": {
          "display_name": "Control",
          "type": "mapping",
          "mandatory": True,
          "filter_by": "_filter_by_control",
      },
      "audit": {
          "display_name": "Audit",
          "mandatory": True,
      },
      "url": "Assessment URL",
      "design": "Conclusion: Design",
      "operationally": "Conclusion: Operation",
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
  def _filter_by_control(cls, predicate):
    return Control.query.filter(
      (Control.id == cls.control_id) &
      (predicate(Control.slug) | predicate(Control.title))
    ).exists()

  @classmethod
  def eager_query(cls):

    query = super(ControlAssessment, cls).eager_query()
    return query.options(orm.subqueryload('control'))

  @classmethod
  def generate_slug_for(cls, obj):
    id = getattr(obj, 'id', uuid1())
    control = getattr(getattr(obj, "control", None), "slug", "")
    obj.slug = "{}.CA-{}".format(control, id)

track_state_for_class(ControlAssessment)
