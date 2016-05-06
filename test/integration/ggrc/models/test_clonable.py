# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

"""Integration test for Clonable mixin"""

from ggrc import db
from ggrc import models

import integration.ggrc
from integration.ggrc import api_helper
from integration.ggrc.models import factories
from integration.ggrc_basic_permissions.models \
    import factories as rbac_factories

from ggrc_basic_permissions.models import Role
from ggrc_basic_permissions.models import UserRole


class TestClonable(integration.ggrc.TestCase):

  """Test case for Clonable mixin"""

  # pylint: disable=invalid-name

  def setUp(self):
    integration.ggrc.TestCase.setUp(self)
    self.client.get("/login")
    self.api_helper = api_helper.Api()

  def clone_object(self, obj, associated_objects=[]):
    # pylint: disable=dangerous-default-value
    return self.api_helper.modify_object(obj, {
        "operation": "clone",
        "associatedObjects": associated_objects
    })

  def test_audit_clone(self):
    """Test that assessment templates get copied correctly"""
    audit = factories.AuditFactory()
    assessment_template_1 = factories.AssessmentTemplateFactory(
        title="test_audit_clone assessment_template_1")
    assessment_template_2 = factories.AssessmentTemplateFactory(
        title="test_audit_clone assessment_template_2")

    factories.RelationshipFactory(
        source=audit,
        destination=assessment_template_1)
    factories.RelationshipFactory(
        source=audit,
        destination=assessment_template_2)

    assessment_template_attributes_def = [
        {
            "definition_type": "assessment_template",
            "definition_id": assessment_template_1.id,
            "title": "test text field",
            "attribute_type": "Text",
            "multi_choice_options": ""
        },
        {
            "definition_type": "assessment_template",
            "definition_id": assessment_template_1.id,
            "title": "test RTF",
            "attribute_type": "Rich Text",
            "multi_choice_options": ""
        },
        {
            "definition_type": "assessment_template",
            "definition_id": assessment_template_1.id,
            "title": "test checkbox",
            "attribute_type": "Checkbox",
            "multi_choice_options": "test checkbox label"
        },
        {
            "definition_type": "assessment_template",
            "definition_id": assessment_template_1.id,
            "title": "test date field",
            "attribute_type": "Date",
            "multi_choice_options": ""
        },
        {
            "definition_type": "assessment_template",
            "definition_id": assessment_template_1.id,
            "title": "test dropdown field",
            "attribute_type": "Dropdown",
            "multi_choice_options": "ddv1,ddv2,ddv3"
        },
    ]

    assessment_template_attributes = []
    for attribute in assessment_template_attributes_def:
      attr = factories.CustomAttributeDefinitionFactory(**attribute)
      assessment_template_attributes += [attr]

    self.clone_object(audit, [u"AssessmentTemplate"])

    self.assertEqual(db.session.query(models.Audit).filter(
        models.Audit.title.like("%copy%")).count(), 1)

    audit_copy = db.session.query(models.Audit).filter(
        models.Audit.title.like("%copy%")).first()

    assessment_templates = audit_copy.related_objects({"AssessmentTemplate"})

    self.assertEqual(len(assessment_templates), 2)

    assessment_template_1 = db.session.query(models.AssessmentTemplate).filter(
        models.AssessmentTemplate.title ==
        "test_audit_clone assessment_template_1"
    ).first()

    self.assertEqual(
        db.session.query(models.CustomAttributeDefinition).filter(
            models.CustomAttributeDefinition.definition_type ==
            "assessment_template",
            models.CustomAttributeDefinition.definition_id ==
            assessment_template_1.id
        ).count(), len(assessment_template_attributes_def))

  def test_audit_clone_auditors(self):
    """Test that auditors get cloned correctly"""
    auditor_role = Role.query.filter_by(name="Auditor").first()

    audit = factories.AuditFactory()
    audit_context = factories.ContextFactory()
    audit.context = audit_context

    users = [
        "user1@example.com",
        "user2@example.com",
        "user3@example.com"
    ]

    auditors = []
    for user in users:
      person = factories.PersonFactory(email=user)
      auditors += [person]

    for auditor in auditors:
      rbac_factories.UserRoleFactory(
          context=audit_context,
          role=auditor_role,
          person=auditor)

    self.assertEqual(
        UserRole.query.filter_by(
            role=auditor_role,
            context=audit.context).count(), 3, "Auditors not present")

    self.clone_object(audit)

    audit_copy = db.session.query(models.Audit).filter(
        models.Audit.title.like("%copy%")).first()

    self.assertEqual(
        UserRole.query.filter_by(
            role=auditor_role,
            context=audit_copy.context
        ).count(), 3, "Auditors not present on copy")

    # Verify that contexts are different for original and copy audit
    another_user_4 = factories.PersonFactory(email="user4@example.com")
    rbac_factories.UserRoleFactory(
        context=audit_context,
        role=auditor_role,
        person=another_user_4)

    self.assertEqual(
        UserRole.query.filter_by(
            role=auditor_role,
            context=audit.context
        ).count(), 4, "Auditors not present")

    self.assertEqual(
        UserRole.query.filter_by(
            role=auditor_role,
            context=audit_copy.context
        ).count(), 3, "Auditors not present on copy")

  def test_audit_clone_custom_attributes(self):
    """Test if custom attributes were copied correctly"""
    audit = factories.AuditFactory()
    ca_def_text = factories.CustomAttributeDefinitionFactory(
        title="test audit CA def 1",
        definition_type="audit",
        attribute_type="Text"
    )
    factories.CustomAttributeValueFactory(
        custom_attribute_id=ca_def_text.id,
        attributable_id=audit.id,
        attributable_type="Audit",
        attribute_value="CA 1 value"
    )

    self.clone_object(audit)

    audit_copy = db.session.query(models.Audit).filter(
        models.Audit.title.like("%copy%")).first()

    self.assertEqual(
        models.CustomAttributeValue.query.filter_by(
            attributable_type="Audit",
            attributable_id=audit_copy.id
        ).count(), 1, "Custom Attribute weren't copied.")
