# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

import datetime
import factory
import random
from factory.base import BaseFactory, FactoryMetaClass, CREATE_STRATEGY
from factory.fuzzy import (
    BaseFuzzyAttribute, FuzzyChoice, FuzzyDate, FuzzyDateTime, FuzzyInteger)
from factory.compat import UTC
from ggrc import models
from ggrc.models.reflection import AttributeInfo


def random_string(prefix='', no_unicode=False):
  return u'{prefix}{suffix}{extra}'.format(
      prefix=prefix,
      suffix=random.randint(0, 9999999999),
      extra='' if no_unicode else u'\xff'
  )


def random_string_attribute(prefix=''):
  return factory.LazyAttribute(lambda m: random_string(prefix))


class FuzzyEmail(BaseFuzzyAttribute):
  def fuzz(self):
    return u"{0}@{1}.{2}".format(
        random_string('user-', True), random_string('domain-', True), 'com')


class FactoryStubMarker(object):
  def __init__(self, class_):
    self.class_ = class_


class FactoryAttributeGenerator(object):
  """Use the SQLAlchemy ORM model to generate factory attributes."""
  @classmethod
  def generate(cls, attrs, model_class, attr):
    """Generate a factory attribute for `attr` by inspecting the mapping
    type of the attribute in `model_class`. Add the attribute to the
    `attrs` dictionary.
    """
    if (hasattr(attr, '__call__')):
      attr_name = attr.attr_name
      value = []
    else:
      attr_name = attr
      class_attr = getattr(model_class, attr_name)
      # look up the class method to use to generate the attribute
      method = getattr(cls, class_attr.__class__.__name__)
      value = method(attr_name, class_attr)
    attrs[attr_name] = value

  @classmethod
  def InstrumentedAttribute(cls, attr_name, class_attr):
    method = getattr(cls, class_attr.property.__class__.__name__)
    return method(attr_name, class_attr)

  @classmethod
  def ColumnProperty(cls, attr_name, class_attr):
    method = getattr(
        cls,
        class_attr.property.expression.type.__class__.__name__,
        cls.default_column_handler)
    return method(attr_name, class_attr)

  @classmethod
  def default_column_handler(cls, attr_name, class_attr):
    return random_string_attribute(attr_name)

  @classmethod
  def DateTime(cls, attr_name, class_attr):
    return FuzzyDateTime(
        datetime.datetime(2013, 1, 1, tzinfo=UTC),
        datetime.datetime.now(UTC) + datetime.timedelta(days=730),
    )

  @classmethod
  def Date(cls, attr_name, class_attr):
    return FuzzyDate(
        datetime.date(2013, 1, 1),
        datetime.date.today() + datetime.timedelta(days=730),
    )

  @classmethod
  def Boolean(cls, attr_name, class_attr):
    return FuzzyChoice([True, False])

  @classmethod
  def Integer(cls, attr_name, class_attr):
    return FuzzyInteger(0, 100000)

  @classmethod
  def RelationshipProperty(cls, attr_name, class_attr):
    if class_attr.property.uselist:
      return []
    else:
      columns = tuple(class_attr.property.local_columns)
      # FIXME: ? Doesn't handle multiple local columns, so won't work for
      #   polymorphic links
      if columns[0].nullable:
        # Not a required association, so skip it
        return None
      elif columns[0].primary_key:
        # This is a 'reverse' association, so skip it (primary keys are
        #   not nullable, but the relationship may still be optional)
        return None
      else:
        return FactoryStubMarker(class_attr.property.mapper.class_)

  @classmethod
  def AssociationProxy(cls, attr_name, class_attr):
    return []

  @classmethod
  def property(cls, attr_name, class_attr):
    return None

  @classmethod
  def simple_property(cls, attr_name, class_attr):
    return None


class ModelFactoryMetaClass(FactoryMetaClass):
  def __new__(cls, class_name, bases, attrs, extra_attrs=None):
    """Use model reflection to build up the list of factory attributes.
    The default attributes can be overridden by defining a subclass
    of `ModelFactory` and defining the attribute to be overriden.
    """
    model_class = attrs.pop('MODEL', None)
    if model_class:
      attrs['FACTORY_FOR'] = dict
      attribute_info = AttributeInfo(model_class)
      for attr in attribute_info._create_attrs:
        if hasattr(attr, '__call__'):
          attr_name = attr.attr_name
        else:
          attr_name = attr
        if attr_name not in attrs:
          FactoryAttributeGenerator.generate(attrs, model_class, attr)
    return super(ModelFactoryMetaClass, cls).__new__(
        cls, class_name, bases, attrs)

ModelFactory = ModelFactoryMetaClass(
    'ModelFactory', (BaseFactory,), {
        'ABSTRACT_FACTORY': True,
        'FACTORY_STRATEGY': CREATE_STRATEGY,
        '__doc__': """ModelFactory base with build and create support.

        This class has supports SQLAlchemy ORM.
        """,
    })


def factory_for(model_class):
  """Get the factory for a model by name or by class.
  If there is a factory defined for this model in globals() that factory
  will be used. Otherwise, one will be created and added to globals().
  """
  if isinstance(model_class, (str, unicode)):
    if '.' in model_class:
      import sys
      path = model_class.split('.')
      module_name = '.'.join(path[:-1])
      factory_name = path[-1]
      __import__(module_name)
      model_class = getattr(sys.modules[module_name], factory_name, None)
    else:
      factory_name = model_class
      import ggrc.models
      model_class = ggrc.models.get_model(model_class)
  else:
    factory_name = model_class.__name__
  factory_name = '{0}Factory'.format(factory_name)
  factory = globals().get(factory_name, None)
  if not factory:
    class model_factory(ModelFactory):
      MODEL = model_class
    model_factory.__name__ = factory_name
    globals()[factory_name] = model_factory
    factory = model_factory
  return factory


class PersonFactory(ModelFactory):
  MODEL = models.Person
  email = FuzzyEmail()


# Governance Objects

class ProgramFactory(ModelFactory):
  MODEL = models.Program
  kind = FuzzyChoice(['Directive', 'Company Controls'])
  status = FuzzyChoice(MODEL.VALID_STATES)


class ContractFactory(ModelFactory):
  MODEL = models.Contract
  kind = FuzzyChoice(MODEL.valid_kinds)
  status = FuzzyChoice(MODEL.VALID_STATES)


class PolicyFactory(ModelFactory):
  MODEL = models.Policy
  kind = FuzzyChoice(MODEL.valid_kinds)
  status = FuzzyChoice(MODEL.VALID_STATES)


class RegulationFactory(ModelFactory):
  MODEL = models.Regulation
  kind = FuzzyChoice(MODEL.valid_kinds)
  status = FuzzyChoice(MODEL.VALID_STATES)


class StandardFactory(ModelFactory):
  MODEL = models.Standard
  kind = FuzzyChoice(MODEL.valid_kinds)
  status = FuzzyChoice(MODEL.VALID_STATES)


class SectionFactory(ModelFactory):
  MODEL = models.Section
  # Explicit `directive` factory is necessary, since it's a `nullable`
  # column, but uses @validate to maintain requirement
  directive = FactoryStubMarker(models.Regulation)


class ClauseFactory(ModelFactory):
  MODEL = models.Clause


class ObjectiveFactory(ModelFactory):
  MODEL = models.Objective
  status = FuzzyChoice(MODEL.VALID_STATES)


class ControlFactory(ModelFactory):
  MODEL = models.Control
  status = FuzzyChoice(MODEL.VALID_STATES)


# Business Objects
class DataAssetFactory(ModelFactory):
  MODEL = models.DataAsset
  status = FuzzyChoice(MODEL.VALID_STATES)


class AccessGroupFactory(ModelFactory):
  MODEL = models.AccessGroup
  status = FuzzyChoice(MODEL.VALID_STATES)


class FacilityFactory(ModelFactory):
  MODEL = models.Facility
  status = FuzzyChoice(MODEL.VALID_STATES)


class MarketFactory(ModelFactory):
  MODEL = models.Market
  status = FuzzyChoice(MODEL.VALID_STATES)


class OrgGroupFactory(ModelFactory):
  MODEL = models.OrgGroup
  status = FuzzyChoice(MODEL.VALID_STATES)


class ProductFactory(ModelFactory):
  MODEL = models.Product
  status = FuzzyChoice(MODEL.VALID_STATES)


class ProjectFactory(ModelFactory):
  MODEL = models.Project
  status = FuzzyChoice(MODEL.VALID_STATES)


class SystemFactory(ModelFactory):
  MODEL = models.System
  status = FuzzyChoice(MODEL.VALID_STATES)


class ProcessFactory(ModelFactory):
  MODEL = models.Process
  status = FuzzyChoice(MODEL.VALID_STATES)


# Audit Objects

class AuditFactory(ModelFactory):
  MODEL = models.Audit
  status = FuzzyChoice(MODEL.VALID_STATES)


class RequestFactory(ModelFactory):
  MODEL = models.Request
  status = FuzzyChoice(MODEL.VALID_STATES)
  request_type = FuzzyChoice(MODEL.VALID_TYPES)


class ResponseFactory(ModelFactory):
  MODEL = models.Response
  status = FuzzyChoice(MODEL.VALID_STATES)


class DocumentationResponseFactory(ResponseFactory):
  MODEL = models.DocumentationResponse
  response_type = 'documentation'


class InterviewResponseFactory(ResponseFactory):
  MODEL = models.InterviewResponse
  response_type = 'interview'


class PopulationSampleResponseFactory(ResponseFactory):
  MODEL = models.PopulationSampleResponse
  response_type = 'population sample'


# Category Objects

class ControlCategoryFactory(ModelFactory):
  MODEL = models.ControlCategory
  type = "ControlCategory"


class ControlAssertionFactory(ModelFactory):
  MODEL = models.ControlAssertion
  type = "ControlAssertion"


# Mapping Objects

class ControlControlFactory(ModelFactory):
  MODEL = models.ControlControl
  status = FuzzyChoice(MODEL.VALID_STATES)


class ControlSectionFactory(ModelFactory):
  MODEL = models.ControlSection
  status = FuzzyChoice(MODEL.VALID_STATES)


class DirectiveControlFactory(ModelFactory):
  MODEL = models.DirectiveControl
  status = FuzzyChoice(MODEL.VALID_STATES)


class ObjectControlFactory(ModelFactory):
  MODEL = models.ObjectControl
  status = FuzzyChoice(MODEL.VALID_STATES)
  controllable = FactoryStubMarker(models.Market)


class ObjectDocumentFactory(ModelFactory):
  MODEL = models.ObjectDocument
  status = FuzzyChoice(MODEL.VALID_STATES)
  documentable = FactoryStubMarker(models.Market)


class ObjectOwnerFactory(ModelFactory):
  MODEL = models.ObjectOwner
  status = FuzzyChoice(MODEL.VALID_STATES)
  ownable = FactoryStubMarker(models.Market)


class ObjectPersonFactory(ModelFactory):
  MODEL = models.ObjectPerson
  status = FuzzyChoice(MODEL.VALID_STATES)
  personable = FactoryStubMarker(models.Market)


class ProgramControlFactory(ModelFactory):
  MODEL = models.ProgramControl
  status = FuzzyChoice(MODEL.VALID_STATES)


class ProgramDirectiveFactory(ModelFactory):
  MODEL = models.ProgramDirective
  status = FuzzyChoice(MODEL.VALID_STATES)


class RelationshipFactory(ModelFactory):
  MODEL = models.Relationship
  status = FuzzyChoice(MODEL.VALID_STATES)
  source = FactoryStubMarker(models.Market)
  destination = FactoryStubMarker(models.Process)


# ggrc_basic_permissions model factories
class RoleFactory(ModelFactory):
  MODEL = models.get_model("Role")


class UserRoleFactory(ModelFactory):
  MODEL = models.get_model("UserRole")


class ContextImplicationFactory(ModelFactory):
  MODEL = models.get_model("ContextImplication")


# ggrc_gdrive_integration model factories
class ObjectFileFactory(ModelFactory):
  MODEL = models.get_model("ObjectFile")
  fileable = FactoryStubMarker(models.DocumentationResponse)


class ObjectFolderFactory(ModelFactory):
  MODEL = models.get_model("ObjectFolder")
  folderable = FactoryStubMarker(models.Audit)


class ObjectEventFactory(ModelFactory):
  MODEL = models.get_model("ObjectEvent")
  eventable = FactoryStubMarker(models.Meeting)
