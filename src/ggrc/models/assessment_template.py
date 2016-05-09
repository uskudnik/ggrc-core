# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: peter@reciprocitylabs.com
# Maintained By: peter@reciprocitylabs.com

"""A module containing the implementation of the assessment template entity."""

from ggrc import db
from ggrc.models import mixins
from ggrc.models import relationship

from ggrc.models.reflection import PublishOnly
from ggrc.models.types import JsonType


class AssessmentTemplate(mixins.Base, mixins.Titled,
                         relationship.Relatable,
                         db.Model):
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
      "Object Contact": "Object Contact",
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

  def get_custom_attributes(self):
    """Get custom attributes defined for certain assessment template"""
    from ggrc.models import CustomAttributeDefinition
    return CustomAttributeDefinition.query.filter(
        CustomAttributeDefinition.definition_type == "assessment_template",
        CustomAttributeDefinition.definition_id == self.id,
    ).all()

  def clone(self, target):
    """Clone Assessment Template and related custom attributes."""
    assessment_template_copy = self._clone()
    rel = relationship.Relationship(
        source=target,
        destination=assessment_template_copy
    )
    db.session.add(rel)
    db.session.flush()

    for cad in self.get_custom_attributes():
      # pylint: disable=protected-access
      cad._clone(assessment_template_copy)

    return (assessment_template_copy, rel)
