# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from integration.ggrc.converters import TestCase
from integration.ggrc.generator import ObjectGenerator

from ggrc.models import AccessGroup
from ggrc.models import Product


class TestImportWithCustomAttributes(TestCase):

  def setUp(self):
    TestCase.setUp(self)
    self.generator = ObjectGenerator()
    self.create_custom_attributes()
    self.create_people()
    self.client.get("/login")

  def tearDown(self):
    pass

  def create_custom_attributes(self):
    gen = self.generator.generate_custom_attribute
    gen("product", attribute_type="Text", title="normal text")
    gen("product", attribute_type="Text", title="man text", mandatory=True)
    gen("product", attribute_type="Rich Text", title="normal RT")
    gen("product", attribute_type="Rich Text", title="man RT", mandatory=True)
    gen("product", attribute_type="Date", title="normal Date")
    gen("product", attribute_type="Date", title="man Date", mandatory=True)
    gen("product", attribute_type="Checkbox", title="normal CH")
    gen("product", attribute_type="Checkbox", title="man CH", mandatory=True)
    gen("product", attribute_type="Dropdown", title="normal select",
        options="a,b,c,d")
    gen("product", attribute_type="Dropdown", title="man select",
        options="e,f,g", mandatory=True)

    gen("access_group", attribute_type="Text",
        title="access group test custom", mandatory=True)

  def create_people(self):
    emails = [
        "user1@ggrc.com",
        "miha@policy.com",
        "someone.else@ggrc.com",
        "another@user.com",
    ]
    for email in emails:
      self.generator.generate_person({
          "name": email.split("@")[0].title(),
          "email": email,
      }, "gGRC Admin")

  def test_product_with_all_custom_attributes(self):
    filename = "product_with_all_custom_attributes.csv"
    response = self.import_file(filename)[0]
    expected_warnings = {
        "Line 6: man CH contains invalid data. The value will be ignored.",
        "Line 8: normal select contains invalid data. The value will be"
        " ignored.",
        "Line 10: man select contains invalid data. The value will be"
        " ignored.",
        "Line 11: normal CH contains invalid data. The value will be ignored.",
        "Line 12: man CH contains invalid data. The value will be ignored.",
        "Line 14: normal Date contains invalid data. The value will be"
        " ignored.",
        "Line 16: man Date contains invalid data. The value will be ignored.",
        "Line 21: Owner field does not contain a valid owner. You will be"
        " assigned as object owner.",
        "Line 22: Specified user 'kr@en.com' does not exist. That user will be"
        " ignored.",
        "Line 22: Owner field does not contain a valid owner. You will be"
        " assigned as object owner.",
        "Line 26: Owner field does not contain a valid owner. You will be"
        " assigned as object owner.",
        "Line 27: Specified user 'user@exameuple.com' does not exist. That"
        " user will be ignored.",
        "Line 27: Owner field does not contain a valid owner. You will be"
        " assigned as object owner."
    }

    expected_errors = {
        "Line 6: Field man CH is required. The line will be ignored.",
        "Line 9: Field man select is required. The line will be ignored.",
        "Line 10: Field man select is required. The line will be ignored.",
        "Line 12: Field man CH is required. The line will be ignored.",
        "Line 16: Field man Date is required. The line will be ignored.",
        "Line 18: Field man RT is required. The line will be ignored.",
        "Line 20: Field man text is required. The line will be ignored.",
        "Line 28: Field Title is required. The line will be ignored."
    }

    self.assertEqual(expected_warnings, set(response["row_warnings"]))
    self.assertEqual(expected_errors, set(response["row_errors"]))
    self.assertEqual(18, response["created"])
    self.assertEqual(8, response["ignored"])
    self.assertEqual(18, Product.query.count())

  def test_multi_word_object_with_custom_attributes(self):
    """Test multi-word (e.g. Access Group, Data Asset) object import"""
    filename = "multi_word_object_custom_attribute_test.csv"
    response = self.import_file(filename)[0]
    self.assertEqual([], response["row_warnings"])
    self.assertEqual([], response["row_errors"])
    self.assertEqual(10, response["created"])
    self.assertEqual(0, response["ignored"])
    self.assertEqual(0, response["updated"])
    self.assertEqual(10, AccessGroup.query.count())

    for x in range(1, 11):
      ag = AccessGroup.query.filter(
        AccessGroup.slug == "ag-{}".format(x)).first()
      self.assertEqual(
        len(filter(lambda v: v.attribute_value == "some text {}".format(x),
                   ag.custom_attribute_values)),
        1
      )
