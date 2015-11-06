# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from ggrc.models import Policy
from ggrc.models import Relationship
from ggrc.converters import errors
from integration.ggrc.converters import TestCase
from integration.ggrc.generator import ObjectGenerator


class TestUnmappings(TestCase):

  def setUp(self):
    TestCase.setUp(self)
    self.generator = ObjectGenerator()
    self.client.get("/login")


  def test_policy_basic_import(self):
    filename = "multi_basic_policy_orggroup_product_with_mappings.csv"
    self.import_file(filename)
    self.assertEqual(Relationship.query.count(), 13)
    filename = "multi_basic_policy_orggroup_product_with_unmappings.csv"
    self.import_file(filename)
    self.assertEqual(Relationship.query.count(), 0)
