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
from ggrc_workflows.models import Workflow, Cycle, TaskGroup, TaskGroupTask
from ggrc_workflows import start_recurring_cycles
from ggrc_workflows.services.workflow_cycle_calculator.weekly_cycle_calculator import WeeklyCycleCalculator

from integration.ggrc_workflows.generator import WorkflowsGenerator
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator

from integration.ggrc_workflows.workflow_cycle_calculator.base_workflow_test_case import BaseWorkflowTestCase


if os.environ.get('TRAVIS', False):
  random.seed(1)  # so we can reproduce the tests if needed

class TestWeeklyWorkflow(BaseWorkflowTestCase):
  def test_relative_to_day(self):
    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "tg_2",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 2, # Tuesday, 9th
            "relative_start_month": None,
            "relative_end_day": 4, # Thursday, 11th
            "relative_end_month": None,
          }
        ],
        "task_group_objects": self.random_objects
      },
      ]
    }
    _, wf = self.generator.generate_workflow(weekly_wf)
    active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()

    rtd = WeeklyCycleCalculator(active_wf).relative_day_to_date

    # Test relative day to date conversion at the start of the week
    with freeze_time("2015-6-8 13:00:00"): # Monday, 6/8/2015
      self.assertEqual(rtd("1"), date(2015, 6, 8))
      self.assertEqual(rtd("2"), date(2015, 6, 9))
      self.assertEqual(rtd("3"), date(2015, 6, 10))
      self.assertEqual(rtd("4"), date(2015, 6, 11))
      self.assertEqual(rtd("5"), date(2015, 6, 12))
      with self.assertRaises(ValueError): rtd("6")
      with self.assertRaises(ValueError): rtd(7)

    # Test relative day to date conversion at the end of the week
    with freeze_time("2015-6-12 13:00:00"): # Friday, 6/12/2015
      self.assertEqual(rtd("1"), date(2015, 6, 8))
      self.assertEqual(rtd("2"), date(2015, 6, 9))
      self.assertEqual(rtd("3"), date(2015, 6, 10))
      self.assertEqual(rtd("4"), date(2015, 6, 11))
      self.assertEqual(rtd("5"), date(2015, 6, 12))

  def test_future_cycle(self):
    """Future cycle workflow

    We create & activate our workflow on Monday and create a workflow
    with one task with start date on Tuesday (tomorrow) and ending on
    Thursday and second task starting on Wednesday and ending on Monday
    (next week).

    Cycle should be generated for the future.
    """
    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "tg_2",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 2, # Tuesday, 9th
            "relative_start_month": None,
            "relative_end_day": 4, # Thursday, 11th
            "relative_end_month": None,
          },
          {
            'title': 'weekly task 2',
            "relative_start_day": 3, # Wednesday, 10th
            "relative_start_month": None,
            "relative_end_day": 1, # 15th, Monday
            "relative_end_month": None,
          }
        ],
        "task_group_objects": self.random_objects
      },
      ]
    }

    with freeze_time("2015-6-8 13:00:00"): # Monday, 6/8/2015
      _, wf = self.generator.generate_workflow(weekly_wf)
      _, tg = self.generator.generate_task_group(wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 9))

      cycles = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date > date(2015, 6, 7))

      self.assertEqual(cycles.count(), 0)

    with freeze_time("2015-6-9 13:00:00"):
      start_recurring_cycles()

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 6, 9)).one()

      self.assertEqual(cycle.start_date, date(2015, 6, 9))
      self.assertEqual(cycle.end_date, date(2015, 6, 15))
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 16))

    with freeze_time("2015-6-16 13:00:00"):
      start_recurring_cycles()

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 6, 16)).one()

      self.assertEqual(cycle.start_date, date(2015, 6, 16))
      self.assertEqual(cycle.end_date, date(2015, 6, 22))
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 23))

  def test_mid_cycle(self):
    """Mid-cycle workflow

    We create & activate our workflow on Wednesday and create a workflow
    with one task with start date on Tuesday (yesterday) and ending on
    Thursday and second task starting on Wednesday and ending on Monday
    (next week).

    Because it's Wednesday, workflow should be activated immediately.
    """
    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "tg_2",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 2, # Tuesday, 9th
            "relative_start_month": None,
            "relative_end_day": 4, # Thursday, 11th
            "relative_end_month": None,
          },
          {
            'title': 'weekly task 2',
            "relative_start_day": 3, # Wednesday, 10th
            "relative_start_month": None,
            "relative_end_day": 1, # 15th, Monday
            "relative_end_month": None,
            }
        ],
        "task_group_objects": self.random_objects
      },
      ]
    }

    with freeze_time("2015-6-10 13:00:00"): # Wednesday, 6/10/2015
      _, wf = self.generator.generate_workflow(weekly_wf)
      _, tg = self.generator.generate_task_group(wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      # Originally this would be 2015-6-10 but because update_workflow_state
      # fixes workflow next_cycle_start_date it's actually 16
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 16))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()

      # Start date should be Tuesday 9th (yesterday), end date should be Monday 15h
      self.assertEqual(cycle.start_date, date(2015, 6, 9))
      self.assertEqual(cycle.end_date, date(2015, 6, 15))

    with freeze_time("2015-6-16 13:00:00"): # Wednesday, 6/10/2015
      start_recurring_cycles()
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 23))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date > date(2015, 6, 15)).one()

      self.assertEqual(cycle.start_date, date(2015, 6, 16))
      self.assertEqual(cycle.end_date, date(2015, 6, 22))

  def test_past_cycle(self):
    """Past workflow

    We create & activate our workflow on Friday and create a workflow
    with one task with start date on Monday and ending on
    Wednesday and second task starting on Tuesday and ending on Thursday.

    Because it's Friday, created cycles should be in the next week.
    """
    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "tg_2",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 1, # Monday, 8th
            "relative_start_month": None,
            "relative_end_day": 3, # Wednesday, 10th
            "relative_end_month": None,
          },
          {
            'title': 'weekly task 2',
            "relative_start_day": 2, # Tuesday, 9th
            "relative_start_month": None,
            "relative_end_day": 4, # 11th, Thursday
            "relative_end_month": None,
            }
        ],
        "task_group_objects": self.random_objects
      },
      ]
    }

    with freeze_time("2015-6-12 13:00:00"): # Friday, 6/12/2015
      _, wf = self.generator.generate_workflow(weekly_wf)
      _, tg = self.generator.generate_task_group(wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 15))

    with freeze_time("2015-6-15 13:00:00"):
      start_recurring_cycles()
      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 6, 15)).one()

      self.assertEqual(cycle.start_date, date(2015, 6, 15))
      self.assertEqual(cycle.end_date, date(2015, 6, 18))

      # Next cycle should start next Tuesday
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 22))

    with freeze_time("2015-6-22 14:00"):
      start_recurring_cycles()
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 29))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 6, 22)).one()

      self.assertEqual(cycle.start_date, date(2015, 6, 22))
      self.assertEqual(cycle.end_date, date(2015, 6, 25))

  def test_type_casting(self):
    """Verify type casting for string input

    Test if string values get converted correctly to integers
    and arithmetic works"""

    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "task group 1",
        "task_group_tasks": [],
        "task_group_objects": self.random_objects
      },
      ]
    }

    task = {
      'title': 'weekly task 1',
      "relative_start_day": "3", # Wed
      "relative_start_month": None,
      "relative_end_day": "5", # Fri
      "relative_end_month": None,
    }

    with freeze_time("2015-7-1 13:00"): # Wed
      _, wf = self.generator.generate_workflow(weekly_wf)

      task_group = db.session.query(TaskGroup).filter(TaskGroup.workflow_id == wf.id).one()
      _, tgt = self.generator.generate_task_group_task(task_group, data=task)

      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()

      self.assertEqual(cycle.start_date, date(2015, 7, 1))
      self.assertEqual(cycle.end_date, date(2015, 7, 2))
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 8))

  def test_adding_task_with_lesser_start_day_after_activating_workflow(self):
    """Test if NCSD gets updated correctly if user adds new task with lesser
    relative start day after workflow has already been activated."""

    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "tg 1",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 5, # Fri, 31st
            "relative_start_month": None,
            "relative_end_day": 3, # Wednesday, August 5th
            "relative_end_month": None,
          }],
        "task_group_objects": []
      },
      ]
    }

    task = {
      'title': 'weekly task 2',
      "relative_start_day": 3,
      "relative_start_month": None,
      "relative_end_day": 4,
      "relative_end_month": None,
    }

    with freeze_time("2015-07-27 13:00"):
      _, wf = self.generator.generate_workflow(weekly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 31))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 31))
      self.assertEqual(cycle.end_date, date(2015, 8, 5))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 7))

      task_group = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()
      _, tgt = self.generator.generate_task_group_task(task_group, data=task)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 5))

  def test_start_workflow_mid_cycle_with_task_before_and_after(self):
    """Test that workflows get triggered correctly if we are in the middle of
    the cycle and there are tasks with start dates before and after."""
    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "tg 1",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 1,
            "relative_end_day": 1,
          }, {
            'title': 'weekly task 2',
            "relative_start_day": 2,
            "relative_end_day": 2,
          }, {
            'title': 'weekly task 3',
            "relative_start_day": 3,
            "relative_end_day": 3,
          }, {
            'title': 'weekly task 4',
            "relative_start_day": 4,
            "relative_end_day": 4,
          }, {
            'title': 'weekly task 5',
            "relative_start_day": 5,
            "relative_end_day": 5,
          }, ],
        "task_group_objects": []
      },
      ]
    }
    with freeze_time("2015-07-29 13:00"): # Wed
      _, wf = self.generator.generate_workflow(weekly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 3))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()
      self.assertEqual(cycle.start_date, date(2015, 7, 27))
      self.assertEqual(cycle.end_date, date(2015, 7, 31))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 8, 3))
      self.assertEqual(cycle.end_date, date(2015, 8, 7))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 10))

  def test_workflow_created_on_weekend_is_scheduled_activate_next_week(self):
    """Test that workflow created during weekend will activate next week"""
    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "tg 1",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 1,
            "relative_start_month": None,
            "relative_end_day": 3,
            "relative_end_month": None,
          }],
        "task_group_objects": []
      },
      ]
    }
    with freeze_time("2015-07-25 13:00"): # Sat
      _, wf = self.generator.generate_workflow(weekly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 27))

  def test_delete_all_tasks_after_cycles_were_already_created_and_create_new_task_group(self):
    """Check that workflow doesn't reset next cycle start date when all tasks are deleted after cycles were already created"""
    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "tg 1",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 3,
            "relative_end_day": 5,
          }],
        "task_group_objects": []
      },
      ]
    }
    new_task_group = {
      "title": "task group 2",
      'task_group_tasks': [
        {
          'title': 'weekly task 1',
          "relative_start_day": 2,
          "relative_end_day": 1,
        }],
      "task_group_objects": []
    }
    with freeze_time("2015-6-9 13:00:00"):  # Tuesday, 6/9/2015
      _, wf = self.generator.generate_workflow(weekly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 10))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 6, 10))
      self.assertEqual(cycle.end_date, date(2015, 6, 12))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 17))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 6, 17))
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 6, 24))
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 1))
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 8))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 15))

      tg = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()

      response = self.generator.api.delete(tg, tg.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, None)

      _, tg = self.generator.generate_task_group(wf, data=new_task_group)
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 14))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 14))
      self.assertEqual(cycle.end_date, date(2015, 7, 20))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 21))

  def test_delete_all_tasks_after_cycles_were_already_created_and_create_new_task_group_start_of_month(self):
    """Check that workflow doesn't reset next cycle start date when all tasks are deleted after cycles were already created"""
    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "tg 1",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 5,
            "relative_end_day": 1,
          }],
        "task_group_objects": []
      },
      ]
    }
    new_task_group = {
      "title": "task group 2",
      'task_group_tasks': [
        {
          'title': 'weekly task 1',
          "relative_start_day": 4,
          "relative_end_day": 5,
        }],
      "task_group_objects": []
    }
    with freeze_time("2015-6-16 13:00:00"):  # Tue, 6/16/2015
      _, wf = self.generator.generate_workflow(weekly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 19))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 6, 19))
      self.assertEqual(cycle.end_date, date(2015, 6, 22))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 26))

      _, cycle = self.generator.generate_cycle(wf) # 2016-6-26

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 2))

      tg = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()

      response = self.generator.api.delete(tg, tg.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, None)

      _, tg = self.generator.generate_task_group(wf, data=new_task_group)
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 2))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 2))
      self.assertEqual(cycle.end_date, date(2015, 7, 2))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 9))

  def test_cycle_start_date_after_task_start_date_moves_backward(self):
    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "tg 1",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 5,
            "relative_start_month": None,
            "relative_end_day": 4,
            "relative_end_month": None,
          }],
        "task_group_objects": []
      },
      ]
    }
    with freeze_time("2015-7-30 13:00:00"):  # Thu, 7/30/2015
      _, wf = self.generator.generate_workflow(weekly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 31))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 31))
      self.assertEqual(cycle.end_date, date(2015, 8, 6))

      _, cycle = self.generator.generate_cycle(wf) # 2015-8-7
      _, cycle = self.generator.generate_cycle(wf) # 2015-8-14
      _, cycle = self.generator.generate_cycle(wf) # 2015-8-21
      _, cycle = self.generator.generate_cycle(wf) # 2015-8-28
      self.assertEqual(cycle.start_date, date(2015, 8, 28))
      self.assertEqual(cycle.end_date, date(2015, 9, 3))

      task_group = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()
      task = db.session.query(TaskGroupTask).filter(
        TaskGroupTask.task_group_id == task_group.id).one()

      self.generator.modify_object(task, {
        "relative_start_day": 1,
        "relative_end_day": 4
      })

      _, cycle = self.generator.generate_cycle(wf) # 2015-8-31
      self.assertEqual(cycle.start_date, date(2015, 8, 31))
      self.assertEqual(cycle.end_date, date(2015, 9, 3))

      _, cycle = self.generator.generate_cycle(wf) # 2015-9-7 is Labour day in US
      self.assertEqual(cycle.start_date, date(2015, 9, 4))
      self.assertEqual(cycle.end_date, date(2015, 9, 10))

      _, cycle = self.generator.generate_cycle(wf) # 2015-9-14
      self.assertEqual(cycle.start_date, date(2015, 9, 14))
      self.assertEqual(cycle.end_date, date(2015, 9, 17))

  def test_create_cycle_manually_start_delete_and_create_task_on_the_same_day(self):
    """Test if NCSD get's calculated correctly if we create a task, manually start the cycle, delete task and recreate task with the same start day"""
    weekly_wf = {
      "title": "weekly thingy",
      "description": "start this many a time",
      "frequency": "weekly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'weekly task 1',
            "relative_start_day": 1,
            "relative_end_day": 1,
          }],
        "task_group_objects": []
      },
      ]
    }

    new_task = {
      'title': 'weekly task 2',
      "relative_start_day": 1,
      "relative_end_day": 1,
    }
    with freeze_time("2015-08-10 05:00"):
      _, wf = self.generator.generate_workflow(weekly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 17))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()
      self.assertEqual(cycle.start_date, date(2015, 8, 10))
      self.assertEqual(cycle.end_date, date(2015, 8, 10))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 8, 17))
      self.assertEqual(cycle.end_date, date(2015, 8, 17))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 24))

      task_group = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()
      old_task = db.session.query(TaskGroupTask).filter(
        TaskGroupTask.task_group_id == task_group.id).one()

      response = self.generator.api.delete(old_task, old_task.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, None)

      _, tgt = self.generator.generate_task_group_task(task_group, data=new_task)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 24))
