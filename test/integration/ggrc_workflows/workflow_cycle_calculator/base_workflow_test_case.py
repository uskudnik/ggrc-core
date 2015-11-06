# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

import random
import copy
from integration.ggrc import TestCase

import os
from ggrc import db
from ggrc_workflows.models import Workflow, TaskGroup, CycleTaskGroupObjectTask, Cycle
from integration.ggrc_workflows.generator import WorkflowsGenerator
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator
from nose.plugins.skip import SkipTest


if os.environ.get('TRAVIS', False):
  random.seed(1)  # so we can reproduce the tests if needed


class BaseWorkflowTestCase(TestCase):
  def setUp(self):
    TestCase.setUp(self)
    self.api = Api()
    self.generator = WorkflowsGenerator()
    self.object_generator = ObjectGenerator()

    self.random_objects = self.object_generator.generate_random_objects()

  def tearDown(self):
    pass