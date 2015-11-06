# coding: utf-8
# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from integration.ggrc import TestCase

from integration.ggrc_workflows.models.factories import CycleTaskFactory
from integration.ggrc_workflows.models.factories import CycleTaskObjectFactory
from ggrc_workflows.notification.data_handler import get_cycle_task_dict


class TestDataHandler(TestCase):

  """ This class test basic functions in the data_handler module """


  def test_get_cycle_task_dict(self):

    ctgo = CycleTaskObjectFactory(title=u"Umbrella \u2062")
    setattr(ctgo, "test_object", None)  # this should be done in the factory
    ct = CycleTaskFactory(cycle_task_group_object=ctgo)
    task_dict = get_cycle_task_dict(ct)

    self.assertEqual(task_dict["object_title"], u"Umbrella \u2062 [deleted]")
