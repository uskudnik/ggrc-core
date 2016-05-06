# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

"""Factories for models"""

import random

import factory

from ggrc import db
from ggrc import models


def random_string(prefix=''):
  return '{prefix}{suffix}'.format(
      prefix=prefix,
      suffix=random.randint(0, 9999999999),
  )


class ModelFactory(factory.Factory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  # modified_by_id = 1

  @classmethod
  def _create(cls, target_class, *args, **kwargs):
    instance = target_class(*args, **kwargs)
    db.session.add(instance)
    db.session.commit()
    return instance


class CustomAttributeDefinitionFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.CustomAttributeDefinition

  title = None
  definition_type = None
  definition_id = None
  attribute_type = None
  multi_choice_options = None


class CustomAttributeValueFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.CustomAttributeValue

  custom_attribute_id = None
  attributable_id = None
  attributable_type = None
  attribute_value = None
  attribute_object_id = None


class TitledFactory(factory.Factory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init
  title = factory.LazyAttribute(lambda m: random_string('title'))


class DirectiveFactory(ModelFactory, TitledFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Directive


class ControlFactory(ModelFactory, TitledFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Control

  directive = factory.SubFactory(DirectiveFactory)
  kind_id = None
  version = None
  documentation_description = None
  verify_frequency_id = None
  fraud_related = None
  key_control = None
  active = None
  notes = None


class AssessmentFactory(ModelFactory, TitledFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Assessment


class ControlCategoryFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.ControlCategory

  name = factory.LazyAttribute(lambda m: random_string('name'))
  lft = None
  rgt = None
  scope_id = None
  depth = None
  required = None


class CategorizationFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Categorization

  category = None
  categorizable = None
  category_id = None
  categorizable_id = None
  categorizable_type = None


class ContextFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Context

  name = factory.LazyAttribute(
      lambda obj: random_string("SomeObjectType Context"))
  related_object = None


class ProgramFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Program

  title = factory.LazyAttribute(lambda _: random_string("program_title"))
  slug = factory.LazyAttribute(lambda _: random_string(""))


class AuditFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Audit

  title = factory.LazyAttribute(lambda _: random_string("title"))
  slug = factory.LazyAttribute(lambda _: random_string(""))
  status = "Planned"
  program_id = factory.LazyAttribute(lambda _: ProgramFactory().id)
  context_id = factory.LazyAttribute(lambda _: ContextFactory().id)


class AssessmentTemplateFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.AssessmentTemplate

  title = factory.LazyAttribute(
      lambda _: random_string("assessment template title"))
  template_object_type = None
  test_plan_procedure = False
  procedure_description = factory.LazyAttribute(
      lambda _: random_string("lorem ipsum description"))
  default_people = \
      "{\"assessors\":\"Object Owners\",\"verifiers\":\"Object Owners\"}"


class ContractFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Contract


class EventFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Event
  revisions = []


class RelationshipFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Relationship
  source = None
  destination = None


class RelationshipAttrFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.RelationshipAttr

  relationship_id = None
  attr_name = None
  attr_value = None


class PersonFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Person
