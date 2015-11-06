# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from ggrc import db
from ggrc.models import ControlAssessment
from integration.ggrc import TestCase
from integration.ggrc.models.factories import ControlAssessmentFactory


class TestControlAssessment(TestCase):

  def test_auto_slug_generation(self):
    ControlAssessmentFactory(title="Some title")
    db.session.commit()
    ca = ControlAssessment.query.first()
    self.assertIn("CONTROL-", ca.slug)
    self.assertIn(ca.control.slug, ca.slug)
