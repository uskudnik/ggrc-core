# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

import random
from integration.ggrc import TestCase
from freezegun import freeze_time
from datetime import date, datetime

import os
from ggrc import db
from ggrc_workflows.models import Workflow, Cycle, TaskGroupTask, TaskGroup, \
  CycleTaskGroupObjectTask
from ggrc_workflows import start_recurring_cycles
from integration.ggrc_workflows.generator import WorkflowsGenerator
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator

from integration.ggrc_workflows.workflow_cycle_calculator.base_workflow_test_case import BaseWorkflowTestCase


if os.environ.get('TRAVIS', False):
  random.seed(1)  # so we can reproduce the tests if needed

class TestMonthlyWorkflow(BaseWorkflowTestCase):
  def test_monthly_workflow(self):
    """Basic monthly workflow test.

    We create a monthly workflow whose cycle should start on 12th and end on
    3rd of next month.
    """
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [
           {
             'title': 'monthly task 1',
             "relative_start_day": 15, # 6/15/2015 Mon
             "relative_start_month": None,
             "relative_end_day": 19, # 6/19/2015 Fri
             "relative_end_month": None,
           },
           {
             'title': 'monthly task 2',
             "relative_start_day": 14, # 6/14/2015 Sun
             "relative_start_month": None,
             "relative_end_day": 3, # 7/3/2015 Fri
             "relative_end_month": None,
           }],
         "task_group_objects": self.random_objects
         },
      ]
    }

    with freeze_time("2015-6-9 13:00:00"): # Tuesday, 6/9/2015
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, tg = self.generator.generate_task_group(wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")

      # Should be 12th, but that is Sunday, so it must be Friday
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 12))

      _, cycle = self.generator.generate_cycle(wf)
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()

      self.assertEqual(cycle.start_date, date(2015, 6, 12))

      # Should be 3rd but 3rd is Independence Day (Observed)
      self.assertEqual(cycle.end_date, date(2015, 7, 2))
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 14))

    with freeze_time("2015-7-14 13:00:00"): # Tuesday, 7/14/2015
      start_recurring_cycles()

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 7, 14)).one()

      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 14)) # 8/14/2015 Friday
      self.assertEqual(cycle.start_date, date(2015, 7, 14)) # 7/10/2015 Fri
      self.assertEqual(cycle.end_date, date(2015, 8, 3)) # 8/3/2015 Mon

  def test_change_task_dates(self):
    """Test if changing the task dates adjusts the next cycle start date
    """
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [
           {
             'title': 'monthly task 1',
             "relative_start_day": 15, # 7/15/2015 Wed
             "relative_start_month": None,
             "relative_end_day": 20, # 7/20/2015 Mon
             "relative_end_month": None,
           }],
         "task_group_objects": self.random_objects
         },
      ]
    }
    with freeze_time("2015-7-1 14:00:00"): # 7/1/2015 Wed
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 15))

      task_group = db.session.query(TaskGroup).filter(TaskGroup.workflow_id == wf.id).one()
      task = db.session.query(TaskGroupTask).filter(TaskGroupTask.task_group_id == task_group.id).one()

      self.generator.modify_object(task, {
        "relative_start_day": 10, # 7/10/2015 Fri
        "relative_end_day": 12 # 7/12/2015 Sun
      })

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 10))

  def test_update_next_cycle_start_date_delete_task(self):
    """Test if deleting a task changes the next cycle start date"""

    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [
           {
             'title': 'monthly task 1',
             "relative_start_day": 15, # 6/15/2015 Mon
             "relative_start_month": None,
             "relative_end_day": 19, # 6/19/2015 Fri
             "relative_end_month": None,
           },
           {
             'title': 'monthly task 2',
             "relative_start_day": 14, # 6/14/2015 Sun
             "relative_start_month": None,
             "relative_end_day": 3, # 7/3/2015 Fri
             "relative_end_month": None,
           }],
         "task_group_objects": self.random_objects
         },
      ]
    }

    with freeze_time("2015-6-9 13:00:00"): # Tuesday, 6/9/2015
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")

      # Should be 14th, but that is Sunday, so it must be Friday
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 12))

      task_group = db.session.query(TaskGroup).filter(TaskGroup.workflow_id == wf.id).one()
      task = db.session.query(TaskGroupTask).filter(
        TaskGroupTask.task_group_id == task_group.id,
        TaskGroupTask.relative_start_day == 14
      ).one()

      response = self.generator.api.delete(task, task.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 15))

  def test_update_next_cycle_start_date_delete_task_group(self):
    """Test if deleting a task group changes next cycle start date"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [
           {
             'title': 'monthly task 1',
             "relative_start_day": 15, # 6/15/2015 Mon
             "relative_start_month": None,
             "relative_end_day": 19, # 6/19/2015 Fri
             "relative_end_month": None,
           }],
         "task_group_objects": self.random_objects
         },
        {"title": "task group 2",
         'task_group_tasks': [
           {
             'title': 'monthly task 2',
             "relative_start_day": 14, # 6/14/2015 Sun
             "relative_start_month": None,
             "relative_end_day": 3, # 7/3/2015 Fri
             "relative_end_month": None,
           }],
         "task_group_objects": self.random_objects
         },
      ]
    }
    with freeze_time("2015-6-9 13:00:00"): # Tuesday, 6/9/2015
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")

      # Should be 14th, but that is Sunday, so it must be Friday
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 12))

      task_group = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id,
        TaskGroup.title == u"task group 2"
      ).one()

      response = self.generator.api.delete(task_group, task_group.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 15))


  def test_update_next_cycle_start_date_new_task_group(self):
    """Check if adding a new task group changes the next cycle start date"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [
           {
             'title': 'monthly task 1',
             "relative_start_day": 15, # 6/15/2015 Mon
             "relative_start_month": None,
             "relative_end_day": 19, # 6/19/2015 Fri
             "relative_end_month": None,
           }],
         "task_group_objects": self.random_objects
         },
      ]
    }
    with freeze_time("2015-6-9 13:00:00"): # Tuesday, 6/9/2015
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")

      # Should be 14th, but that is Sunday, so it must be Friday
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 15))

      _, tg = self.generator.generate_task_group(wf, data=
        {"title": "task group 2",
         'task_group_tasks': [
           {
             'title': 'monthly task 2',
             "relative_start_day": 14, # 6/14/2015 Sun
             "relative_start_month": None,
             "relative_end_day": 3, # 7/3/2015 Fri
             "relative_end_month": None,
           }],
         "task_group_objects": self.random_objects
         })

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 12))

  def test_delete_all_tasks(self):
    """Check that workflow doesn't have next cycle start date when all tasks are deleted"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [
           {
             'title': 'monthly task 1',
             "relative_start_day": 15, # 6/15/2015 Mon
             "relative_start_month": None,
             "relative_end_day": 19, # 6/19/2015 Fri
             "relative_end_month": None,
           }],
         "task_group_objects": self.random_objects
         },
      ]
    }
    with freeze_time("2015-6-9 13:00:00"): # Tuesday, 6/9/2015
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 15))

      task_group = db.session.query(TaskGroup).filter(TaskGroup.workflow_id == wf.id).one()

      response = self.generator.api.delete(task_group, task_group.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, None)

  def test_type_casting(self):
    """Verify type casting for string input

    Test if string values get converted correctly to integers
    and arithmetic works"""

    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [],
         "task_group_objects": self.random_objects
         },
      ]
    }

    task = {
      'title': 'monthly task 1',
      "relative_start_day": "15", # 7/15/2015 Wed
      "relative_start_month": None,
      "relative_end_day": "19", # 7/19/2015 Sun
      "relative_end_month": None,
    }

    with freeze_time("2015-7-1 13:00"): # Wed
      _, wf = self.generator.generate_workflow(monthly_workflow)

      task_group = db.session.query(TaskGroup).filter(TaskGroup.workflow_id == wf.id).one()
      _, tgt = self.generator.generate_task_group_task(task_group, data=task)

      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")


    with freeze_time("2015-7-15 13:00"): # Wed
      start_recurring_cycles()

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()

      self.assertEqual(cycle.start_date, date(2015, 7, 15))
      self.assertEqual(cycle.end_date, date(2015, 7, 17)) # 19 is Sun
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 14)) # 15 is Sat


  def test_ncsd_in_previous_month_automatic(self):
    """Check starting cycles on periodic basis with one of next cycle start dates in previous month"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {
          "title": "task group 1",
          'task_group_tasks': [
            {
              'title': 'monthly task 1',
              "relative_start_day": 1, # 7/10/2015 Fri
              "relative_start_month": None,
              "relative_end_day": 15, # 7/15/2015 Wed
              "relative_end_month": None,
            },
            {
              'title': 'monthly task 2',
              "relative_start_day": 10, # 7/10/2015 Fri
              "relative_start_month": None,
              "relative_end_day": 15, # 7/15/2015 Wed
              "relative_end_month": None,
            }],
          "task_group_objects": self.random_objects
        },
      ]
    }

    with freeze_time("2015-5-30 14:00"):
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")

      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 1))

    ###### Jun

    with freeze_time("2015-6-1 01:00"):
      start_recurring_cycles()

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 1))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 6, 1)).one()

      self.assertEqual(cycle.start_date, date(2015, 6, 1))
      self.assertEqual(cycle.end_date, date(2015, 6, 15))

    ##### Jul

    with freeze_time("2015-7-1 01:00"):
      start_recurring_cycles()

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 31))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 7, 1)).one()

      self.assertEqual(cycle.start_date, date(2015, 7, 1))
      self.assertEqual(cycle.end_date, date(2015, 7, 15))

    ###### Aug

    with freeze_time("2015-7-31 01:00"):
      start_recurring_cycles()

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 9, 1))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 7, 31)).one()

      self.assertEqual(cycle.start_date, date(2015, 7, 31))
      self.assertEqual(cycle.end_date, date(2015, 8, 14))

    ###### Sept

    with freeze_time("2015-9-1 01:00"):
      start_recurring_cycles()

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 1))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 9, 1)).one()

      self.assertEqual(cycle.start_date, date(2015, 9, 1))
      self.assertEqual(cycle.end_date, date(2015, 9, 15))

  def test_manual_starting_cycles_ncsd_in_previous_month(self):
    """Check starting cycles manually with one next cycle start date in the previous month"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {
          "title": "task group 1",
          'task_group_tasks': [
            {
              'title': 'monthly task 1',
              "relative_start_day": 10, # 7/10/2015 Fri
              "relative_start_month": None,
              "relative_end_day": 15, # 7/15/2015 Wed
              "relative_end_month": None,
            }],
          "task_group_objects": self.random_objects
        },
      ]
    }

    task = {
      'title': 'monthly task 2',
      "relative_start_day": 1, # 7/10/2015 Fri
      "relative_start_month": None,
      "relative_end_day": 15, # 7/15/2015 Wed
      "relative_end_month": None,
    }
    with freeze_time("2015-7-1 13:00:00"): # 7/1/2015 Wed
      # We start with a single task from 10-15
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")

      # First cycle should start on 10th
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 10))

      # We add another task that starts on 1st (today)
      task_group = db.session.query(TaskGroup).filter(TaskGroup.workflow_id == wf.id).one()
      _, tgt = self.generator.generate_task_group_task(task_group, data=task)

      # Workflow should have one active cycle and
      # next cycle start date at the start of August
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 31))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 7, 1)).one()

      self.assertEqual(cycle.start_date, date(2015, 7, 1))
      self.assertEqual(cycle.end_date, date(2015, 7, 15))

      ###### Aug
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 31))
      self.assertEqual(cycle.end_date, date(2015, 8, 14))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 9, 1))

      ###### Sep
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 9, 1))
      self.assertEqual(cycle.end_date, date(2015, 9, 15))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 1))

      ###### Oct
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 10, 1))
      self.assertEqual(cycle.end_date, date(2015, 10, 15))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 30))

      ###### Nov
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 10, 30))
      self.assertEqual(cycle.end_date, date(2015, 11, 13))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 12, 1))

      ###### Dec
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 12, 1))
      self.assertEqual(cycle.end_date, date(2015, 12, 15))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 12, 30))

      ###### Jan
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 12, 30))
      self.assertEqual(cycle.end_date, date(2016, 1, 15))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 2, 1))

  def test_start_date_late_in_month(self):
    """Check that workflows start as expected if start date is 29th"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {
          "title": "task group 1",
          'task_group_tasks': [
            {
              'title': 'monthly task 1',
              "relative_start_day": 29,
              "relative_start_month": None,
              "relative_end_day": 31,
              "relative_end_month": None,
            }],
          "task_group_objects": self.random_objects
        },
      ]
    }

    with freeze_time("2015-1-20 13:00"):
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")

      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 1, 29))

    # January
    with freeze_time("2015-1-29 14:00"):
      start_recurring_cycles()

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 2, 27))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 1, 29)).one()

      self.assertEqual(cycle.start_date, date(2015, 1, 29))
      self.assertEqual(cycle.end_date, date(2015, 1, 30))

    # February
    with freeze_time("2015-2-27 14:00"):
      start_recurring_cycles()

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 3, 27))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 2, 27)).one()

      self.assertEqual(cycle.start_date, date(2015, 2, 27))
      self.assertEqual(cycle.end_date, date(2015, 2, 27))

    # March
      with freeze_time("2015-3-27 14:00"):
        start_recurring_cycles()

        active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
        self.assertEqual(active_wf.next_cycle_start_date, date(2015, 4, 29))

        cycle = db.session.query(Cycle).filter(
          Cycle.workflow_id == wf.id,
          Cycle.start_date == date(2015, 3, 27)).one()

        self.assertEqual(cycle.start_date, date(2015, 3, 27))
        self.assertEqual(cycle.end_date, date(2015, 3, 31))

    # April
      with freeze_time("2015-4-29 14:00"):
        start_recurring_cycles()

        active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
        self.assertEqual(active_wf.next_cycle_start_date, date(2015, 5, 29))

        cycle = db.session.query(Cycle).filter(
          Cycle.workflow_id == wf.id,
          Cycle.start_date == date(2015, 4, 29)).one()

        self.assertEqual(cycle.start_date, date(2015, 4, 29))
        self.assertEqual(cycle.end_date, date(2015, 4, 30))

  def test_changing_end_date_when_tasks_deleted(self):
    """Test that deleting cycle task correctly adjusts cycle end date"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {
          "title": "task group 1",
          'task_group_tasks': [
            {
              'title': 'monthly task 1',
              "relative_start_day": 15,
              "relative_start_month": None,
              "relative_end_day": 20,
              "relative_end_month": None,
            }, {
              'title': 'monthly task 2',
              "relative_start_day": 18,
              "relative_start_month": None,
              "relative_end_day": 25,
              "relative_end_month": None,
            }],
          "task_group_objects": []
        },
      ]
    }
    with freeze_time("2015-07-15 13:00"):
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")

      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 14))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 7, 15)).one()
      self.assertEqual(cycle.start_date, date(2015, 7, 15))
      self.assertEqual(cycle.end_date, date(2015, 7, 24))

      cycle_task = db.session.query(CycleTaskGroupObjectTask).filter(
        CycleTaskGroupObjectTask.cycle_id == cycle.id,
        CycleTaskGroupObjectTask.title == "monthly task 2"
      ).one()

      response = self.generator.api.delete(cycle_task, cycle_task.id)
      self.assert200(response)

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()
      self.assertEqual(cycle.start_date, date(2015, 7, 15))
      self.assertEqual(cycle.end_date, date(2015, 7, 20))

  def test_adding_task_with_lesser_start_day_after_activating_workflow(self):
    """Test if NCSD gets updated correctly if user adds new task with smaller
    relative start day after workflow has already been activated."""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {
          "title": "task group 1",
          'task_group_tasks': [
            {
              'title': 'monthly task 1',
              "relative_start_day": 30,
              "relative_start_month": None,
              "relative_end_day": 7,
              "relative_end_month": None,
            }],
          "task_group_objects": []
        },
      ]
    }

    task = {
      'title': 'monthly task 2',
      "relative_start_day": 20,
      "relative_start_month": None,
      "relative_end_day": 22,
      "relative_end_month": None,
    }
    with freeze_time("2015-07-27 13:00"):
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 30))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 30))
      self.assertEqual(cycle.end_date, date(2015, 8, 7))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 28))

      # We add another task that starts on 20th
      task_group = db.session.query(TaskGroup).filter(TaskGroup.workflow_id == wf.id).one()
      _, tgt = self.generator.generate_task_group_task(task_group, data=task)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 20))

  def test_delete_task_after_workflow_has_been_activated(self):
    """Test that next cycle start date gets recalculated corrently if first
    task has been deleted after cycle has already started"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {
          "title": "task group 1",
          'task_group_tasks': [
            {
              'title': 'monthly task 1',
              "relative_start_day": 24,
              "relative_start_month": None,
              "relative_end_day": 28,
              "relative_end_month": None,
            }, {
              'title': 'monthly task 2',
              "relative_start_day": 27,
              "relative_start_month": None,
              "relative_end_day": 29,
              "relative_end_month": None,
            }],
          "task_group_objects": []
        },
      ]
    }

    with freeze_time("2015-07-22 13:00"):
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 24))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 24))
      self.assertEqual(cycle.end_date, date(2015, 7, 29))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 24))

      task_group = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()

      task = db.session.query(TaskGroupTask).filter(
        TaskGroupTask.task_group_id == task_group.id,
        TaskGroupTask.title == "monthly task 1"
      ).one()

      response = self.generator.api.delete(task, task.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 27))

  def test_start_workflow_mid_cycle_with_task_before_and_after(self):
    """Test that workflows get triggered correctly if we are in the middle of the cycle and there are tasks with start dates before and after."""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {
          "title": "task group 1",
          'task_group_tasks': [
            {
              'title': 'monthly task 1',
              "relative_start_day": 1,
              "relative_end_day": 1,
            }, {
              'title': 'monthly task 2',
              "relative_start_day": 2,
              "relative_end_day": 2,
            }, {
              'title': 'monthly task 3',
              "relative_start_day": 3,
              "relative_end_day": 3,
            }, {
              'title': 'monthly task 4',
              "relative_start_day": 4,
              "relative_end_day": 4,
            }, {
              'title': 'monthly task 5',
              "relative_start_day": 5,
              "relative_end_day": 5,
            }],
          "task_group_objects": []
        },
      ]
    }
    with freeze_time("2015-08-03 13:00"):
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 9, 1))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()
      self.assertEqual(cycle.start_date, date(2015, 7, 31))
      self.assertEqual(cycle.end_date, date(2015, 8, 5))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 9, 1))
      self.assertEqual(cycle.end_date, date(2015, 9, 4))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 1))

  def test_delete_all_tasks_after_cycles_were_already_created_and_create_new_task_group(self):
    """Check that workflow doesn't reset next cycle start date when all tasks are deleted after cycles were already created"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [
           {
             'title': 'monthly task 1',
             "relative_start_day": 15,  # 6/15/2015 Mon
             "relative_end_day": 19,  # 6/19/2015 Fri
           }],
         "task_group_objects": self.random_objects
         },
      ]
    }

    new_task_group = {
      "title": "task group 2",
      'task_group_tasks': [
        {
          'title': 'monthly task 1',
          "relative_start_day": 13,
          "relative_end_day": 7,
        }],
      "task_group_objects": []
    }

    with freeze_time("2015-6-9 13:00:00"):  # Tuesday, 6/9/2015
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 15))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 6, 15))
      self.assertEqual(cycle.end_date, date(2015, 6, 19))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 15))

      _, cycle = self.generator.generate_cycle(wf) # Jul
      _, cycle = self.generator.generate_cycle(wf) # Aug

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 9, 15))

      tg = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()

      response = self.generator.api.delete(tg, tg.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, None)

      _, tg = self.generator.generate_task_group(wf, data=new_task_group)
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 9, 11))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 9, 11))
      self.assertEqual(cycle.end_date, date(2015, 10, 7))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 13))

  def test_delete_all_tasks_after_cycles_were_already_created_no_new_tasks_created_until_NCSD(self):
    """Check that workflow doesn't reset next cycle start date when all tasks are deleted after cycles were already created"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [
           {
             'title': 'monthly task 1',
             "relative_start_day": 15,  # 6/15/2015 Mon
             "relative_end_day": 19,  # 6/19/2015 Fri
           }],
         "task_group_objects": self.random_objects
         },
      ]
    }

    with freeze_time("2015-6-9 13:00:00"):  # Tuesday, 6/9/2015
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 15))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 6, 15))
      self.assertEqual(cycle.end_date, date(2015, 6, 19))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 15))

      _, cycle = self.generator.generate_cycle(wf)  # Jul
      _, cycle = self.generator.generate_cycle(wf)  # Aug

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 9, 15))

      tg = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()

      response = self.generator.api.delete(tg, tg.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, None)

    with freeze_time("2015-9-15 13:00"):
      start_recurring_cycles()

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
      )
      self.assertEqual(cycle.count(), 3)

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 9, 15)
      )
      self.assertEqual(cycle.count(), 0)

  def test_setup_tasks_didnt_get_deleted_cycle_tasks_got_deleted(self):
    """Test usecase where user deletes latest cycle's tasks but NOT setup tasks"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [
           {
             'title': 'monthly task 1',
             "relative_start_day": 15,  # 6/15/2015 Mon
             "relative_end_day": 19,  # 6/19/2015 Fri
           }, {
             'title': 'monthly task 2',
             "relative_start_day": 17,  # 6/17/2015 Wed
             "relative_end_day": 23,  # 6/23/2015 Tue
           }],
         "task_group_objects": []
         },
      ]
    }
    with freeze_time("2015-6-9 13:00:00"):
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 15))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 6, 15))
      self.assertEqual(cycle.end_date, date(2015, 6, 23))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 15))
      self.assertEqual(cycle.end_date, date(2015, 7, 23))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 8, 14))
      self.assertEqual(cycle.end_date, date(2015, 8, 21))

      cycle_task_1 = db.session.query(CycleTaskGroupObjectTask).filter(
        CycleTaskGroupObjectTask.cycle_id == cycle.id,
        CycleTaskGroupObjectTask.start_date == date(2015, 8, 14),
        CycleTaskGroupObjectTask.title == "monthly task 1"
      ).one()

      cycle_task_2 = db.session.query(CycleTaskGroupObjectTask).filter(
        CycleTaskGroupObjectTask.cycle_id == cycle.id,
        CycleTaskGroupObjectTask.start_date == date(2015, 8, 17),
        CycleTaskGroupObjectTask.title == "monthly task 2"
      ).one()

      self.assertEqual(cycle.is_current, True)

      response = self.generator.api.delete(cycle_task_1, cycle_task_1.id)
      self.assert200(response)

      response = self.generator.api.delete(cycle_task_2, cycle_task_2.id)
      self.assert200(response)

      cycle = db.session.query(Cycle).filter(Cycle.id == cycle.id).one()
      self.assertEqual(cycle.is_current, False)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 9, 15))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 9, 15))
      self.assertEqual(cycle.end_date, date(2015, 9, 23))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 15))

  def test_setup_tasks_deleted_last_cycle_tasks_deleted(self):
    """Test usecase where user deletes latest cycle's tasks AND setup tasks"""
    monthly_workflow = {
      "title": "monthly test wf",
      "description": "start this many a time",
      "frequency": "monthly",
      "task_groups": [
        {"title": "task group 1",
         'task_group_tasks': [
           {
             'title': 'monthly task 1',
             "relative_start_day": 15,  # 6/15/2015 Mon
             "relative_end_day": 19,  # 6/19/2015 Fri
           }, {
             'title': 'monthly task 2',
             "relative_start_day": 17,  # 6/17/2015 Wed
             "relative_end_day": 23,  # 6/23/2015 Tue
           }],
         "task_group_objects": []
         },
      ]
    }

    new_task_group = {"title": "new task group 2",
     'task_group_tasks': [
       {
         'title': 'monthly task 2',
         "relative_start_day": 5,
         "relative_end_day": 10,
       }],
     "task_group_objects": []
     }

    with freeze_time("2015-6-9 13:00:00"):
      # Lets activate the workflow and generate a couple of cycles...
      _, wf = self.generator.generate_workflow(monthly_workflow)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 15))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 6, 15))
      self.assertEqual(cycle.end_date, date(2015, 6, 23))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 15))
      self.assertEqual(cycle.end_date, date(2015, 7, 23))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 8, 14))
      self.assertEqual(cycle.end_date, date(2015, 8, 21))

      # Delete the task group and verify that there is no next cycle start date
      tg = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()

      response = self.generator.api.delete(tg, tg.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, None)

      # Remove last cycle's tasks
      self.assertEqual(cycle.is_current, True)
      cycle_task_1 = db.session.query(CycleTaskGroupObjectTask).filter(
        CycleTaskGroupObjectTask.cycle_id == cycle.id,
        CycleTaskGroupObjectTask.start_date == date(2015, 8, 14),
        CycleTaskGroupObjectTask.title == "monthly task 1"
      ).one()
      response = self.generator.api.delete(cycle_task_1, cycle_task_1.id)
      self.assert200(response)

      cycle = db.session.query(Cycle).filter(Cycle.id == cycle.id).one()
      self.assertEqual(cycle.start_date, date(2015, 8, 17))

      cycle_task_2 = db.session.query(CycleTaskGroupObjectTask).filter(
        CycleTaskGroupObjectTask.cycle_id == cycle.id,
        CycleTaskGroupObjectTask.start_date == date(2015, 8, 17),
        CycleTaskGroupObjectTask.title == "monthly task 2"
      ).one()
      response = self.generator.api.delete(cycle_task_2, cycle_task_2.id)
      self.assert200(response)

      # Verify cycle got completed
      cycle = db.session.query(Cycle).filter(Cycle.id == cycle.id).one()
      self.assertEqual(cycle.is_current, False)

      _, tg = self.generator.generate_task_group(wf, data=new_task_group)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 5))
