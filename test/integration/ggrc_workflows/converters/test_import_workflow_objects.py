# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

from datetime import date

from os.path import abspath
from os.path import dirname
from os.path import join

from integration.ggrc.converters import TestCase

from ggrc import db
from ggrc_workflows.models.task_group import TaskGroup
from ggrc_workflows.models.task_group_object import TaskGroupObject
from ggrc_workflows.models.task_group_task import TaskGroupTask
from ggrc_workflows.models.workflow import Workflow

THIS_ABS_PATH = abspath(dirname(__file__))


class TestWorkflowObjectsImport(TestCase):

  """
    Test imports for basic workflow objects
  """

  def setUp(self):
    TestCase.setUp(self)
    self.client.get("/login")
    self.CSV_DIR = join(THIS_ABS_PATH, "test_csvs/")

  def test_full_good_import_no_warnings(self):
    filename = "simple_workflow_test_no_warnings.csv"
    response = self.import_file(filename)
    messages = ("block_errors", "block_warnings", "row_errors", "row_warnings")

    broken_imports = set([
        "Control Assessment",
        "Task Group Task",
    ])

    for block in response:
      if block["name"] in broken_imports:
        continue
      for message in messages:
        self.assertEqual(set(), set(block[message]))

    self.assertEqual(1, Workflow.query.count())
    self.assertEqual(1, TaskGroup.query.count())
    self.assertEqual(1, TaskGroupTask.query.count())
    self.assertEqual(2, TaskGroupObject.query.count())


  def test_import_task_date_format(self):
    """Test import of tasks for workflows with various frequencies"""
    filename = "data_for_workflow_export_testing.csv"
    response = self.import_file(filename)
    objects = {"Workflow", "Task Group", "Task Group Task"}
    messages = ["block_errors", "block_warnings", "row_errors", "row_warnings",
                "ignored"]
    # Assert that there were no import errors
    for obj in response:
      if obj['name'] in objects:
        self.assertEqual([[], [], [], [], 0], [obj[msg] for msg in messages])

    # Assert that CSV import got imported correctly
    getters = {
      "one_time": lambda task: (task.start_date, task.end_date),
      "weekly": lambda task: (task.relative_start_day, task.relative_end_day),
      "monthly": lambda task: (task.relative_start_day, task.relative_end_day),
      "quarterly": lambda task: ((task.relative_start_month,
                                  task.relative_start_day),
                                 (task.relative_end_month,
                                  task.relative_end_day)),
      "annually": lambda task: ((task.relative_start_month,
                                 task.relative_start_day),
                                (task.relative_end_month,
                                 task.relative_end_day))
    }

    tasks = [
      ["task-1", "one_time", (date(2015, 7, 1), date(2015, 7, 15))],
      ["task-2", "weekly", (2, 5)],
      ["task-3", "monthly", (1, 22)],
      ["task-4", "quarterly", ((1, 5), (2, 15))],
      ["task-5", "annually", ((5, 7), (7, 15))],
    ]

    for t in tasks:
      slug, freq, result = t
      task = db.session.query(TaskGroupTask).filter(
        TaskGroupTask.slug == slug).one()
      getter = getters[freq]
      self.assertEqual(task.task_group.workflow.frequency, freq)
      self.assertEqual(getter(task), result,
        "Failed importing data for task with slug = '{}'".format(slug))
