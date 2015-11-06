# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: andraz@reciprocitylabs.com
# Maintained By: andraz@reciprocitylabs.com

from ggrc import db
from ggrc.models.mixins import Base
from ggrc.models.relationship import Relationship
from ggrc.models.relationship import RelationshipAttr
from integration.ggrc import TestCase
import ggrc
import ggrc.builder
import ggrc.services
import random
import werkzeug.exceptions


class RelationshipTestMockModel(Base, ggrc.db.Model):
  __tablename__ = 'relationship_test_mock_model'
  foo = db.Column(db.String)

  # REST properties
  _publish_attrs = ['modified_by_id', 'foo']
  _update_attrs = ['foo']

  @staticmethod
  def _validate_relationship_attr(cls, source, destination, name, value):
    if cls.__name__ not in {source.type, destination.type}:
      return False
    if name != "validated_attr":
      return False
    try:
      int(value)
    except ValueError:
      return False
    return True


class TestRelationship(TestCase):

  def setUp(self):
    super(TestRelationship, self).setUp()
    if RelationshipTestMockModel.__table__.exists(db.engine):
      RelationshipTestMockModel.__table__.drop(db.engine)
    RelationshipTestMockModel.__table__.create(db.engine)
    with self.client.session_transaction() as session:
      session['permissions'] = {
          "__GGRC_ADMIN__": {"__GGRC_ALL__": {"contexts": [0]}}
      }

  def mock_model(self, id=None, modified_by_id=1, **kwarg):
    if 'id' not in kwarg:
      kwarg['id'] = random.randint(0, 999999999)
    if 'modified_by_id' not in kwarg:
      kwarg['modified_by_id'] = 1
    mock = RelationshipTestMockModel(**kwarg)
    return mock

  def test_attrs_validation(self):
    m1 = self.mock_model()
    m2 = self.mock_model()
    rel = Relationship(source=m1, destination=m2)
    with self.assertRaises(werkzeug.exceptions.BadRequest):
      rel.attrs["foo"] = "bar"
    with self.assertRaises(werkzeug.exceptions.BadRequest):
      rel.attrs["validated_attr"] = "wrong value"
    rel.attrs["validated_attr"] = "123"


class TestRelationshipAttr(TestCase):

  def test_gather_validators(self):
    class ValidatorParent(object):
      @staticmethod
      def _validate_relationship_attr(cls):
        return True

    class ValidatorChild(ValidatorParent):
      @staticmethod
      def _validate_relationship_attr(cls):
        return False

    validators = RelationshipAttr._gather_validators(ValidatorChild)
    self.assertEqual({True, False}, {v() for v in validators})
