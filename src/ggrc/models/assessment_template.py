# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""A module containing the implementation of the assessment template entity."""

from ggrc import db
from ggrc.models import mixins
from ggrc.models.mixins import Base, Titled, CustomAttributable
from ggrc.models.audit import Audit
from ggrc.models.custom_attribute_definition import CustomAttributeDefinition
from ggrc.models.reflection import PublishOnly
from ggrc.models import relationship
from ggrc.models.types import JsonType
from ggrc.services import common
from ggrc.services import signals

from sqlalchemy.orm import validates

class AssessmentTemplate(relationship.Relatable, mixins.Titled,
                         mixins.CustomAttributable, mixins.Slugged, db.Model):
  """A class representing the assessment template entity.

  An Assessment Template is a template that allows users for easier creation of
  multiple Assessments that are somewhat similar to each other, avoiding the
  need to repeatedly define the same set of properties for every new Assessment
  object.
  """
  __tablename__ = "assessment_templates"

  # the type of the object under assessment
  template_object_type = db.Column(db.String, nullable=True)

  # whether to use the control test plan as a procedure
  test_plan_procedure = db.Column(db.Boolean, nullable=False)

  # procedure description
  procedure_description = db.Column(db.Text, nullable=True)

  # the people that should be assigned by default to each assessment created
  # within the releated audit
  default_people = db.Column(JsonType, nullable=False)

  # labels to show to the user in the UI for various default people values
  DEFAULT_PEOPLE_LABELS = {
      "Object Owners": "Object Owners",
      "Audit Lead": "Audit Lead",
      "Auditors": "Auditors",
      "Primary Assessor": "Principal Assessor",
      "Secondary Assessors": "Secondary Assessors",
      "Primary Contact": "Primary Contact",
      "Secondary Contact": "Secondary Contact",
  }

  _title_uniqueness = False

  # REST properties
  _publish_attrs = [
      "template_object_type",
      "test_plan_procedure",
      "procedure_description",
      "default_people",
      PublishOnly("DEFAULT_PEOPLE_LABELS")
  ]

  @classmethod
  def generate_slug_prefix_for(cls, obj):
    return "TEMPLATE"

  def _clone(self):
    """Clone Assessment Template.

    Returns:
      Instance of assessment template copy.
    """
    data = {
        "title": self.title,
        "template_object_type": self.template_object_type,
        "test_plan_procedure": self.test_plan_procedure,
        "procedure_description": self.procedure_description,
        "default_people": self.default_people,
    }
    assessment_template_copy = AssessmentTemplate(**data)
    db.session.add(assessment_template_copy)
    db.session.flush()
    return assessment_template_copy

  def clone(self, target):
    """Clone Assessment Template and related custom attributes."""
    assessment_template_copy = self._clone()
    rel = relationship.Relationship(
        source=target,
        destination=assessment_template_copy
    )
    db.session.add(rel)
    db.session.flush()

    for cad in self.custom_attribute_definitions:
      # pylint: disable=protected-access
      cad._clone(assessment_template_copy)

    return (assessment_template_copy, rel)

  @validates("mandatory")
  def validate_mandatory(self, key, value):
    print "validate_mandatory", key, value
    return value

  @validates("multi_choice_options")
  def validate_multi_choice_options(self, key, value):
    print "validate_multi_choice_options", key, value

  @validates("multi_choice_mandatory")
  def validate_multi_choice_mandatory(self, key, value):
    print "validate_multi_choice_mandatory", key, value


def create_audit_relationship(audit_stub, obj):
  audit = Audit.query.get(audit_stub["id"])

  rel = relationship.Relationship(
    source=audit,
    destination=obj,
    context=audit.context)
  db.session.add(rel)

def create_custom_attribute_definition(obj, data):
  del data['opts']
  mandatory = data["mandatory"] if "mandatory" in data else False
  update = {
    "mandatory": mandatory,
    "definition_type": "assessment_template",
    "definition_id": obj.id,
  }
  data.update(update)
  custom_attr_def = CustomAttributeDefinition(**data)
  db.session.add(custom_attr_def)


def create_custom_attribute_definitions(obj, custom_attribute_definitions):
  print "\n"*5
  print "create_custom_attribute_definitions"
  for cad in custom_attribute_definitions:
    print "cad: ", cad
    create_custom_attribute_definition(obj, cad)


@common.Resource.model_posted.connect_via(AssessmentTemplate)
def handle_assessment_template(sender, obj=None, src=None, service=None):
  db.session.flush()
  print "handle_assessment_template", obj.id
  print src

  if "audit" in src:
    create_audit_relationship(src["audit"], obj)

  if ("custom_attribute_definitions" in src and
      src["custom_attribute_definitions"]):
    create_custom_attribute_definitions(obj, src["custom_attribute_definitions"])

  db.session.flush()
