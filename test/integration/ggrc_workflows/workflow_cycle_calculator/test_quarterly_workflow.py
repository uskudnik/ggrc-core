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
from integration.ggrc_workflows.generator import WorkflowsGenerator
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator

from integration.ggrc_workflows.workflow_cycle_calculator.base_workflow_test_case import BaseWorkflowTestCase
from ggrc_workflows.services.workflow_cycle_calculator import \
  QuarterlyCycleCalculator


if os.environ.get('TRAVIS', False):
  random.seed(1)  # so we can reproduce the tests if needed

class TestQuarterlyWorkflow(BaseWorkflowTestCase):
  """Test quarterly workflow

  All test cases based on spec.
  """
  def test_relative_day_to_date(self):
    """Verify relative_day_to_date conversion for all possible quarterly scenarios"""
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 30,
            "relative_start_month": 1,
            "relative_end_day": 15,
            "relative_end_month": 1,
          }],
        "task_group_objects": self.random_objects
      },
      ]
    }
    _, wf = self.generator.generate_workflow(quarterly_wf)
    _, awf = self.generator.activate_workflow(wf)
    active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()

    QuarterlyCycleCalculator.__abstractmethods__ = set()
    qcc = QuarterlyCycleCalculator(active_wf)

    rdd = qcc.relative_day_to_date

    # Test first-quarter option conversion
    # 1/1 in first quarter
    test_and_expected_dates = [
      ((2015, 1, 1), (2015, 1, 1)),
      ((2015, 2, 1), (2015, 1, 1)),
      ((2015, 3, 1), (2015, 1, 1)),
      ((2015, 4, 1), (2015, 4, 1)),
      ((2015, 5, 1), (2015, 4, 1)),
      ((2015, 6, 1), (2015, 4, 1)),
      ((2015, 7, 1), (2015, 7, 1)),
      ((2015, 8, 1), (2015, 7, 1)),
      ((2015, 9, 1), (2015, 7, 1)),
      ((2015, 10, 1), (2015, 10, 1)),
      ((2015, 11, 1), (2015, 10, 1)),
      ((2015, 12, 1), (2015, 10, 1))
    ]
    for test_date, expected_date in test_and_expected_dates:
      self.assertEqual(
        rdd(relative_day=1, relative_month=1, base_date=date(*test_date)),
        date(*expected_date))

    #########################################################################
    test_and_expected_dates = [
      ((2015, 1, 1), (2014, 11, 1)),
      ((2015, 2, 1), (2015, 2, 1)),
      ((2015, 3, 1), (2015, 2, 1)),
      ((2015, 4, 1), (2015, 2, 1)),
      ((2015, 5, 1), (2015, 5, 1)),
      ((2015, 6, 1), (2015, 5, 1)),
      ((2015, 7, 1), (2015, 5, 1)),
      ((2015, 8, 1), (2015, 8, 1)),
      ((2015, 9, 1), (2015, 8, 1)),
      ((2015, 10, 1), (2015, 8, 1)),
      ((2015, 11, 1), (2015, 11, 1)),
      ((2015, 12, 1), (2015, 11, 1)),
      ((2016, 1, 1), (2015, 11, 1))
    ]
    for test_date, expected_date in test_and_expected_dates:
      self.assertEqual(
        rdd(relative_day=1, relative_month=2, base_date=date(*test_date)),
        date(*expected_date))

    #########################################################################
    test_and_expected_dates = [
      ((2015, 1, 1), (2014, 12, 1)),
      ((2015, 2, 1), (2014, 12, 1)),
      ((2015, 3, 1), (2015, 3, 1)),
      ((2015, 4, 1), (2015, 3, 1)),
      ((2015, 5, 1), (2015, 3, 1)),
      ((2015, 6, 1), (2015, 6, 1)),
      ((2015, 7, 1), (2015, 6, 1)),
      ((2015, 8, 1), (2015, 6, 1)),
      ((2015, 9, 1), (2015, 9, 1)),
      ((2015, 10, 1), (2015, 9, 1)),
      ((2015, 11, 1), (2015, 9, 1)),
      ((2015, 12, 1), (2015, 12, 1)),
      ((2016, 1, 1), (2015, 12, 1)),
      ((2016, 2, 1), (2015, 12, 1))
    ]
    for test_date, expected_date in test_and_expected_dates:
      self.assertEqual(
        rdd(relative_day=1, relative_month=3, base_date=date(*test_date)),
        date(*expected_date))

  def test_start_wf_1_1(self):
    """Test quarterly WF 1/1 activating through months"""
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 1,
            "relative_end_day": 1,
            "relative_end_month": 1,
          }],
        "task_group_objects": []
      },
      ]
    }
    base_dates = [(2014, 12, 1),
                  (2015, 1, 1), (2015, 2, 1), (2015, 3, 1),
                  (2015, 4, 1), (2015, 5, 1), (2015, 6, 1),
                  (2015, 7, 1), (2015, 8, 1), (2015, 9, 1),
                  (2015, 10, 1), (2015, 11, 1), (2015, 12, 1)]
    expected_dates = [(2015, 1, 1),
                      (2015, 4, 1), (2015, 4, 1), (2015, 4, 1),
                      (2015, 7, 1), (2015, 7, 1), (2015, 7, 1),
                      (2015, 10, 1), (2015, 10, 1), (2015, 10, 1),
                      (2016, 1, 1), (2016, 1, 1), (2016, 1, 1)]

    for i, bd in enumerate(base_dates):
      with freeze_time("{} 13:00".format(date(*bd))):
        _, wf = self.generator.generate_workflow(quarterly_wf)
        _, awf = self.generator.activate_workflow(wf)
        active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
        self.assertEqual(active_wf.non_adjusted_next_cycle_start_date,
                         date(*expected_dates[i]))

  def test_start_wf_2_1(self):
    """Test quarterly WF 2/1 activating through months"""
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 2,
            "relative_end_day": 1,
            "relative_end_month": 2,
          }],
        "task_group_objects": []
      },
      ]
    }
    base_dates = [(2014, 12, 1),
                  (2015, 1, 1), (2015, 2, 1), (2015, 3, 1),
                  (2015, 4, 1), (2015, 5, 1), (2015, 6, 1),
                  (2015, 7, 1), (2015, 8, 1), (2015, 9, 1),
                  (2015, 10, 1), (2015, 11, 1), (2015, 12, 1)]
    expected_dates = [(2015, 2, 1),
                      (2015, 2, 1), (2015, 5, 1), (2015, 5, 1),
                      (2015, 5, 1), (2015, 8, 1), (2015, 8, 1),
                      (2015, 8, 1), (2015, 11, 1), (2015, 11, 1),
                      (2015, 11, 1), (2016, 2, 1), (2016, 2, 1)]

    for i, bd in enumerate(base_dates):
      with freeze_time("{} 13:00".format(date(*bd))):
        _, wf = self.generator.generate_workflow(quarterly_wf)
        _, awf = self.generator.activate_workflow(wf)
        active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
        self.assertEqual(active_wf.non_adjusted_next_cycle_start_date,
                         date(*expected_dates[i]))

  def test_start_wf_3_1(self):
    """Test quarterly WF 3/1 activating through months"""
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 3,
            "relative_end_day": 1,
            "relative_end_month": 3,
          }],
        "task_group_objects": []
      },
      ]
    }
    base_dates = [(2014, 12, 1),
                  (2015, 1, 1), (2015, 2, 1), (2015, 3, 1),
                  (2015, 4, 1), (2015, 5, 1), (2015, 6, 1),
                  (2015, 7, 1), (2015, 8, 1), (2015, 9, 1),
                  (2015, 10, 1), (2015, 11, 1), (2015, 12, 1)]
    expected_dates = [(2015, 3, 1),
                      (2015, 3, 1), (2015, 3, 1), (2015, 6, 1),
                      (2015, 6, 1), (2015, 6, 1), (2015, 9, 1),
                      (2015, 9, 1), (2015, 9, 1), (2015, 12, 1),
                      (2015, 12, 1), (2015, 12, 1), (2016, 3, 1)]


    for i, bd in enumerate(base_dates):
      with freeze_time("{} 13:00".format(date(*bd))):
        _, wf = self.generator.generate_workflow(quarterly_wf)
        _, awf = self.generator.activate_workflow(wf)
        active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
        self.assertEqual(active_wf.non_adjusted_next_cycle_start_date,
                         date(*expected_dates[i]))

  def test_equal_month_end_day_before_start_day(self):
    """
    relative_start_month == relative_end_month
    relative_start_day > relative_end_day

    Task 1: 1/30 => 1/15: Same month number but next quarter, relative_end_day < relative_start_day
    Jan 30 -> Apr 15h
    Apr 30 -> Jul 15
    Jul 30 -> Oct 15
    Oct 30 -> Jan 15
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 30,
            "relative_start_month": 1,
            "relative_end_day": 15,
            "relative_end_month": 1,
          }],
        "task_group_objects": self.random_objects
      },
      ]
    }
    with freeze_time("2015-6-8 13:00:00"): # Mon, 6/8/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 30))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()

      self.assertEqual(cycle.start_date, date(2015, 4, 30))
      self.assertEqual(cycle.end_date, date(2015, 7, 15))

  def test_equal_month_end_day_after_start_day(self):
    """
    relative_start_month == relative_end_month
    relative_start_day < relative_end_day

    Task 2: 2/11 => 2/19: Same month number within a quarter, relative_start_day < relative_end_day
    Feb 11 -> Feb 19
    May 11 -> May 19
    Aug 11 -> Aug 19
    Nov 11 -> Nov 19
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 11,
            "relative_start_month": 2,
            "relative_end_day": 19,
            "relative_end_month": 2,
          }],
        "task_group_objects": self.random_objects
      },
      ]
    }
    with freeze_time("2015-6-8 13:00:00"): # Mon, 6/8/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 11))

    with freeze_time("2015-8-11 13:00:00"):
      start_recurring_cycles()

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()

      self.assertEqual(cycle.start_date, date(2015, 8, 11))
      self.assertEqual(cycle.end_date, date(2015, 8, 19))

  def test_equal_month_start_day_equal_month_day(self):
    """
    relative_start_month == relative_end_month
    relative_start_day == relative_end_day

    Task 3: 3/15 => 3/15: Same month number within a quarter, relative_start_day == relative_end_day
    Mar 15 -> Mar 15
    Jun 15 -> Jun 15
    Sep 15 -> Sep 15
    Dec 15 -> Dec 15
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 15,
            "relative_start_month": 3,
            "relative_end_day": 15,
            "relative_end_month": 3,
          }],
        "task_group_objects": self.random_objects
      },
      ]
    }
    with freeze_time("2015-6-8 13:00:00"): # Mon, 6/8/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 6, 15))

    with freeze_time("2015-6-15 13:00:00"):
      start_recurring_cycles()

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 6, 15)).one()

      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 9, 15))
      self.assertEqual(cycle.start_date, date(2015, 6, 15))
      self.assertEqual(cycle.end_date, date(2015, 6, 15))

    with freeze_time("2015-6-19 13:00:00"):
      _, cycle = self.generator.generate_cycle(wf)

      self.assertEqual(cycle.start_date, date(2015, 9, 15))
      self.assertEqual(cycle.end_date, date(2015, 9, 15))

      _, cycle = self.generator.generate_cycle(wf)
      _, cycle = self.generator.generate_cycle(wf)

      self.assertEqual(cycle.start_date, date(2016, 3, 15))
      self.assertEqual(cycle.end_date, date(2016, 3, 15))

  def test_diff_month_start_day_before_end_day(self):
    """
    relative_start_month != relative_end_month
    relative_start_day < relative_end_day

    Task 4: 1/15 => 2/18: Different month number within the same quarter, relative_start_day < relative_end_day
    Jan 15 -> Feb 18
    Apr 15 -> May 18
    Jul 15 -> Aug 18
    Oct 15 -> Nov 18
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 15,
            "relative_start_month": 1,
            "relative_end_day": 18,
            "relative_end_month": 2,
          }],
        "task_group_objects": self.random_objects
      },
      ]
    }
    with freeze_time("2015-6-8 13:00:00"): # Mon, 6/8/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 15))

    with freeze_time("2015-7-15 13:00:00"):
      start_recurring_cycles()

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()

      self.assertEqual(cycle.start_date, date(2015, 7, 15))
      self.assertEqual(cycle.end_date, date(2015, 8, 18))

  def test_diff_month_start_day_after_end_day(self):
    """
    relative_start_month != relative_end_month
    relative_start_day < relative_end_day

    Task 5: 1/20 => 3/5: Different month number within the same quarter, relative_end_day < relative_start_day
    Jan 20 -> Mar 5
    Apr 20 -> Jun 5
    Jul 20 -> Sep 5
    Oct 20 -> Dec 5
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 20,
            "relative_start_month": 1,
            "relative_end_day": 5,
            "relative_end_month": 3,
          }],
        "task_group_objects": self.random_objects
      },
      ]
    }
    with freeze_time("2015-6-8 13:00:00"): # Mon, 6/8/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 20))

    with freeze_time("2015-7-20 13:00:00"):
      start_recurring_cycles()

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()

      self.assertEqual(cycle.start_date, date(2015, 7, 20))
      self.assertEqual(cycle.end_date, date(2015, 9, 4))

  def test_too_long_month(self):
    """Test too big date behaviour

    Test round down if the month doesn't have enough days (e.g. February)

    Task 5: 2/30 => 2/31:
    Aug 28 -> Aug 31
    Nov 30 -> Nov 30
    Feb 29 -> Feb 29 (2016)
    May 30 -> May 31 (2016)
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 30,
            "relative_start_month": 2,
            "relative_end_day": 31,
            "relative_end_month": 2,
          }],
        "task_group_objects": self.random_objects
      },
      ]
    }

    with freeze_time("2015-6-20 13:00:00"):
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 8, 28))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 8, 28))
      self.assertEqual(cycle.end_date, date(2015, 8, 31))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 11, 30))
      self.assertEqual(cycle.end_date, date(2015, 11, 30))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2016, 2, 29))
      self.assertEqual(cycle.end_date, date(2016, 2, 29))

      _, cycle = self.generator.generate_cycle(wf)
      # May 30 2016 is US Memorial Day
      self.assertEqual(cycle.start_date, date(2016, 5, 27))
      self.assertEqual(cycle.end_date, date(2016, 5, 31))

  def test_type_casting(self):
    """Verify type casting for string input

    Test if string values get converted correctly to integers
    and arithmetic works"""
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [],
        "task_group_objects": self.random_objects
      }]}

    task = {
     'title': 'quarterly task 1',
     "relative_start_day": "1",
     "relative_start_month": "1",
     "relative_end_day": "8",
     "relative_end_month": "2",
     }
    with freeze_time("2015-7-1 13:00"):
      _, wf = self.generator.generate_workflow(quarterly_wf)

      task_group = db.session.query(TaskGroup).filter(TaskGroup.workflow_id == wf.id).one()
      _, tgt = self.generator.generate_task_group_task(task_group, data=task)

      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()

      self.assertEqual(cycle.start_date, date(2015, 7, 1))
      self.assertEqual(cycle.end_date, date(2015, 8, 7)) # 8/8/2015 is Sat
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 1))

  def test_start_date_got_adjusted_to_previous_month(self):
    """Test quarterly month calculating logic when start date got adjusted to previous month"""

    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 2,
            "relative_end_day": 1,
            "relative_end_month": 1,
          }],
        "task_group_objects": self.random_objects
      },
      ]
    }
    with freeze_time("2015-7-5 13:00"):
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 31))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 31))
      self.assertEqual(cycle.end_date, date(2015, 10, 1))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 30))

    with freeze_time("2015-10-30 13:00"):
      start_recurring_cycles()

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 2, 1))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id,
        Cycle.start_date == date(2015, 10, 30)).one()

      self.assertEqual(cycle.start_date, date(2015, 10, 30))
      self.assertEqual(cycle.end_date, date(2015, 12, 30))

  def test_edit_activated_workflow_should_not_adjust_next_cycle_start_date(self):
    """Test editing activated workflow - it shouldn't move next cycle start date

    Test editing activated workflow - it should not move next cycle start date
    unless cycle was manually activated, it should only adjust next cycle start
    date while taking into consideration current tasks."""
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 1,
            "relative_end_day": 24,
            "relative_end_month": 3,
          }],
        "task_group_objects": self.random_objects
      },
      ]
    }
    with freeze_time("2015-07-22 13:00"):
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 1))

      task_group = db.session.query(TaskGroup).filter(TaskGroup.workflow_id == wf.id).one()
      task = db.session.query(TaskGroupTask).filter(TaskGroupTask.task_group_id == task_group.id).one()

      self.generator.modify_object(task, {
        "relative_start_day": 2,  # 10/2/2015 Fri
        "relative_end_day": 24
      })

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 2))

      self.generator.modify_object(task, {
        "relative_start_day": 3,  # 10/3/2015 Sat
        "relative_end_day": 24
      })

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 2)) # 10/3/2015 Sat

      self.generator.modify_object(task, {
        "relative_start_day": 5,  # 10/3/2015 Sat
        "relative_end_day": 24
      })

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 5)) # 10/5/2015 Mon

  def test_editing_activated_workflow_when_dates_changed_after_manually_starting(self):
    """Test editing activated workflow - it should never set a next cycle start date in the past

    After editing a task and manually starting two cycles, we re-edit the task
    and verify that the new next cycle start date is NOT reset.
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 1,
            "relative_end_day": 24,
            "relative_end_month": 3,
          }],
        "task_group_objects": self.random_objects
      },
      ]
    }

    with freeze_time("2015-07-22 13:00"):
      # First we create the workflow
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 1))

      # Second we edit the workflow and verify NCSD is correctly adjusted
      task_group = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()
      task = db.session.query(TaskGroupTask).filter(
        TaskGroupTask.task_group_id == task_group.id).one()

      self.generator.modify_object(task, {
        "relative_start_day": 2,  # 10/2/2015 Fri
        "relative_end_day": 24
      })

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 2))

      # Third, we manually start two cycles
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 10, 2))
      self.assertEqual(cycle.end_date, date(2015, 12, 22))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 12, 30))
      self.assertEqual(cycle.end_date, date(2016, 3, 24))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 4, 1)) #4/2/2016 Sat

      # We now edit relative start day, it should be 8th of April
      self.generator.modify_object(task, {
        "relative_start_day": 8,
        "relative_end_day": 24
      })

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date,
                       date(2016, 4, 8))  # 4/8/2016 Fri

      # Test if NCSD gets adjusted correctly also if new NCSD is less than old
      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2016, 4, 8))
      self.assertEqual(cycle.end_date, date(2016, 6, 24))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date,
                       date(2016, 7, 8))  # 7/8/2016 Fri

      self.generator.modify_object(task, {
        "relative_start_day": 2, # 7/2/2016 Sat
        "relative_end_day": 24
      })

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date,
                       date(2016, 7, 1))  # 7/1/2016 Fri

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2016, 7, 1))
      self.assertEqual(cycle.end_date, date(2016, 9, 23)) # 9/24/2015 Sat

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date,
                       date(2016, 9, 30))  # 10/1/2016 Sat

  def test_adding_task_with_lesser_start_day_after_activating_workflow(self):
    """Test if NCSD gets updated correctly if user adds new task with lesser
    relative start day after workflow has already been activated."""
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 30,
            "relative_start_month": 1,
            "relative_end_day": 7,
            "relative_end_month": 2,
          }],
        "task_group_objects": []
      },
      ]
    }

    task = {
      'title': 'quarterly task 2',
      "relative_start_day": 20,
      "relative_start_month": 1,
      "relative_end_day": 22,
      "relative_end_month": 2,
    }

    with freeze_time("2015-07-27 13:00"):
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 30))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 30))
      self.assertEqual(cycle.end_date, date(2015, 8, 7))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 30))

      # We add another task that starts on 20th
      task_group = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()
      _, tgt = self.generator.generate_task_group_task(task_group, data=task)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 20))

  def test_start_workflow_mid_cycle_with_task_before_and_after(self):
    """Test that workflows get triggered correctly if we are in the middle of
    the cycle and there are tasks with start dates before and after."""
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 1,
            "relative_end_day": 1,
            "relative_end_month": 1,
          }, {
            'title': 'quarterly task 2',
            "relative_start_day": 2,
            "relative_start_month": 1,
            "relative_end_day": 2,
            "relative_end_month": 1,
          }, {
            'title': 'quarterly task 3',
            "relative_start_day": 3,
            "relative_start_month": 1,
            "relative_end_day": 3,
            "relative_end_month": 1,
          }, {
            'title': 'quarterly task 4',
            "relative_start_day": 4,
            "relative_start_month": 1,
            "relative_end_day": 4,
            "relative_end_month": 1,
          }, {
            'title': 'quarterly task 5',
            "relative_start_day": 6,
            "relative_start_month": 1,
            "relative_end_day": 6,
            "relative_end_month": 1,
          }],
        "task_group_objects": []
      },
      ]
    }
    with freeze_time("2015-07-03"):
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 1))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()
      self.assertEqual(cycle.start_date, date(2015, 7, 1))
      self.assertEqual(cycle.end_date, date(2015, 7, 6))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 10, 1))
      self.assertEqual(cycle.end_date, date(2015, 10, 6))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 12, 30))

  def test_delete_all_tasks_after_cycles_were_already_created_and_create_new_task_group(self):
    """Check that workflow doesn't reset next cycle start date when all tasks are deleted after cycles were already created"""
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 15,
            "relative_start_month": 1,
            "relative_end_day": 19,
            "relative_end_month": 2,
          }],
        "task_group_objects": []
      },
      ]
    }


    new_task_group = {
      "title": "task group 2",
      'task_group_tasks': [
        {
          'title': 'annually task 1',
          "relative_start_day": 13,
          "relative_start_month": 1,
          "relative_end_day": 17,
          "relative_end_month": 1,
        }],
      "task_group_objects": []
    }
    with freeze_time("2015-6-9 13:00:00"):  # Tuesday, 6/9/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 15))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2015, 7, 15))
      self.assertEqual(cycle.end_date, date(2015, 8, 19))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 10, 15))

      _, cycle = self.generator.generate_cycle(wf)  # Oct
      _, cycle = self.generator.generate_cycle(wf)  # Jan

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 4, 15))

      tg = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == wf.id).one()

      response = self.generator.api.delete(tg, tg.id)
      self.assert200(response)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, None)

      _, tg = self.generator.generate_task_group(wf, data=new_task_group)
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 4, 13))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2016, 4, 13))
      self.assertEqual(cycle.end_date, date(2016, 4, 15))

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 7, 13))

  def test_multiple_task_groups_multiple_tasks_multiple_quarters_future(self):
    """Test behaviour of multiple task groups with multiple tasks spread across multiple quarters

    Task group  | Tasks | Start day           | End day
    1           | 1     | Feb/May/Aug/Nov  1  | Feb/May/Aug/Nov  5
    1           | 2     | Feb/May/Aug/Nov 10  | Feb/May/Aug/Nov 20
    2           | 3     | Feb/May/Aug/Nov 20  | Feb/May/Aug/Nov 25
    2           | 4     | Mar/Jun/Sep/Dec  1  | Mar/Jun/Sep/Dec  5

    Cycle should last from:
    Feb 1 - Mar 5
    May 1 - Jun 5
    Aug 1 - Sep 5
    Nov 1 - Dec 5
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 2,
            "relative_end_day": 5,
            "relative_end_month": 2,
          }, {
            'title': 'quarterly task 2',
            "relative_start_day": 10,
            "relative_start_month": 2,
            "relative_end_day": 20,
            "relative_end_month": 2,
          }],
        "task_group_objects": []
      }, {
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 3',
            "relative_start_day": 20,
            "relative_start_month": 2,
            "relative_end_day": 25,
            "relative_end_month": 2,
          }, {
            'title': 'quarterly task 4',
            "relative_start_day": 1,
            "relative_start_month": 3,
            "relative_end_day": 5,
            "relative_end_month": 3,
          }],
        "task_group_objects": []
      }]
    }

    with freeze_time("2015-6-9 13:00:00"):  # Tuesday, 6/9/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 31))

      dates = [
        ((2015, 7, 31), (2015, 9, 4), (2015, 10, 30)),
        ((2015, 10, 30), (2015, 12, 4), (2016, 2, 1)),
        ((2016, 2, 1), (2016, 3, 4), (2016, 4, 29)),
        ((2016, 4, 29), (2016, 6, 3), (2016, 8, 1)),
        ((2016, 8, 1), (2016, 9, 2), (2016, 11, 1)),
        ((2016, 11, 1), (2016, 12, 5), (2017, 2, 1)),
        ((2017, 2, 1), (2017, 3, 3), (2017, 5, 1)),
        ((2017, 5, 1), (2017, 6, 5), (2017, 8, 1)),
        ((2017, 8, 1), (2017, 9, 5), (2017, 11, 1)),
        ((2017, 11, 1), (2017, 12, 5), (2018, 2, 1)),
        ((2018, 2, 1), (2018, 3, 5), (2018, 5, 1)),
        ((2018, 5, 1), (2018, 6, 5), (2018, 8, 1)),
      ]
      for csd, ced, ncsd in dates:
        _, cycle = self.generator.generate_cycle(wf)
        self.assertEqual(cycle.start_date, date(*csd))
        self.assertEqual(cycle.end_date, date(*ced))
        active_wf = db.session.query(Workflow).filter(
          Workflow.id == wf.id).one()
        self.assertEqual(active_wf.next_cycle_start_date, date(*ncsd))

  def test_multiple_task_groups_multiple_tasks_multiple_quarters_in_middle(self):
    """Test behaviour of multiple task groups with multiple tasks spread across multiple quarters

    Task group  | Tasks | Start day           | End day
    1           | 1     | Feb/May/Aug/Nov  1  | Feb/May/Aug/Nov  5
    1           | 2     | Feb/May/Aug/Nov 10  | Feb/May/Aug/Nov 20
    2           | 3     | Feb/May/Aug/Nov 20  | Feb/May/Aug/Nov 25
    2           | 4     | Mar/Jun/Sep/Dec  1  | Mar/Jun/Sep/Dec  5

    Cycle should last from:
    Feb 1 - Mar 5
    May 1 - Jun 5
    Aug 1 - Sep 5
    Nov 1 - Dec 5
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 2,
            "relative_end_day": 5,
            "relative_end_month": 2,
          }, {
            'title': 'quarterly task 2',
            "relative_start_day": 10,
            "relative_start_month": 2,
            "relative_end_day": 20,
            "relative_end_month": 2,
          }],
        "task_group_objects": []
      }, {
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 3',
            "relative_start_day": 20,
            "relative_start_month": 2,
            "relative_end_day": 25,
            "relative_end_month": 2,
          }, {
            'title': 'quarterly task 4',
            "relative_start_day": 1,
            "relative_start_month": 3,
            "relative_end_day": 5,
            "relative_end_month": 3,
          }],
        "task_group_objects": []
      }]
    }
    with freeze_time("2015-6-3 13:00:00"):  # Tuesday, 6/3/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 31))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()
      self.assertEqual(cycle.start_date, date(2015, 5, 1))
      self.assertEqual(cycle.end_date, date(2015, 6, 5))

      dates = [
        ((2015, 7, 31), (2015, 9, 4), (2015, 10, 30)),
        ((2015, 10, 30), (2015, 12, 4), (2016, 2, 1)),
        ((2016, 2, 1), (2016, 3, 4), (2016, 4, 29)),
        ((2016, 4, 29), (2016, 6, 3), (2016, 8, 1)),
      ]
      for csd, ced, ncsd in dates:
        _, cycle = self.generator.generate_cycle(wf)
        self.assertEqual(cycle.start_date, date(*csd))
        self.assertEqual(cycle.end_date, date(*ced))
        active_wf = db.session.query(Workflow).filter(
          Workflow.id == wf.id).one()
        self.assertEqual(active_wf.next_cycle_start_date, date(*ncsd))

  def test_multiple_task_groups_multiple_tasks_multiple_quarters_last_quarter_middle(self):
    """Test behaviour of multiple task groups with multiple tasks spread across multiple quarters

    Task group  | Tasks | Start day           | End day
    1           | 1     | Feb/May/Aug/Nov  1  | Feb/May/Aug/Nov  5
    1           | 2     | Feb/May/Aug/Nov 10  | Feb/May/Aug/Nov 20
    2           | 3     | Feb/May/Aug/Nov 20  | Feb/May/Aug/Nov 25
    2           | 4     | Mar/Jun/Sep/Dec  1  | Mar/Jun/Sep/Dec  5

    Cycle should last from:
    Feb 1 - Mar 5
    May 1 - Jun 5
    Aug 1 - Sep 5
    Nov 1 - Dec 5
    """
    quarterly_wf = {
      "title": ("quarterly thingy test_multiple_task_groups_multiple_tasks_"
               "multiple_quarters_last_quarter_middle"),
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 2,
            "relative_end_day": 5,
            "relative_end_month": 2,
          }, {
            'title': 'quarterly task 2',
            "relative_start_day": 10,
            "relative_start_month": 2,
            "relative_end_day": 20,
            "relative_end_month": 2,
          }],
        "task_group_objects": []
      }, {
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 3',
            "relative_start_day": 20,
            "relative_start_month": 2,
            "relative_end_day": 25,
            "relative_end_month": 2,
          }, {
            'title': 'quarterly task 4',
            "relative_start_day": 1,
            "relative_start_month": 3,
            "relative_end_day": 5,
            "relative_end_month": 3,
          }],
        "task_group_objects": []
      }]
    }
    with freeze_time("2015-12-01 13:00:00"):  # Tuesday, 12/1/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 2, 1))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()
      self.assertEqual(cycle.start_date, date(2015, 10, 30))
      self.assertEqual(cycle.end_date, date(2015, 12, 4))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2016, 2, 1))
      self.assertEqual(cycle.end_date, date(2016, 3, 4))
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 4, 29))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2016, 4, 29))
      self.assertEqual(cycle.end_date, date(2016, 6, 3))
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 8, 1))

  def test_multiple_task_groups_multiple_tasks_multiple_quarters_last_quarter_past(self):
    """Test behaviour of multiple task groups with multiple tasks spread across multiple quarters

    Task group  | Tasks | Start day           | End day
    1           | 1     | Feb/May/Aug/Nov  1  | Feb/May/Aug/Nov  5
    1           | 2     | Feb/May/Aug/Nov 10  | Feb/May/Aug/Nov 20
    2           | 3     | Feb/May/Aug/Nov 20  | Feb/May/Aug/Nov 25
    2           | 4     | Mar/Jun/Sep/Dec  1  | Mar/Jun/Sep/Dec  5

    Cycle should last from:
    Feb 1 - Mar 5
    May 1 - Jun 5
    Aug 1 - Sep 5
    Nov 1 - Dec 5
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 2,
            "relative_end_day": 5,
            "relative_end_month": 2,
          }, {
            'title': 'quarterly task 2',
            "relative_start_day": 10,
            "relative_start_month": 2,
            "relative_end_day": 20,
            "relative_end_month": 2,
          }],
        "task_group_objects": []
      }, {
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 3',
            "relative_start_day": 20,
            "relative_start_month": 2,
            "relative_end_day": 25,
            "relative_end_month": 2,
          }, {
            'title': 'quarterly task 4',
            "relative_start_day": 1,
            "relative_start_month": 3,
            "relative_end_day": 5,
            "relative_end_month": 3,
          }],
        "task_group_objects": []
      }]
    }
    with freeze_time("2015-12-7 13:00:00"):  # Mon, 12/7/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 2, 1))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2016, 2, 1))
      self.assertEqual(cycle.end_date, date(2016, 3, 4))
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 4, 29))

      _, cycle = self.generator.generate_cycle(wf)
      self.assertEqual(cycle.start_date, date(2016, 4, 29))
      self.assertEqual(cycle.end_date, date(2016, 6, 3))
      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.next_cycle_start_date, date(2016, 8, 1))

  def test_multiple_task_groups_multiple_tasks_multiple_quarters_tasks_in_reverse_order(self):
    """Test behaviour of multiple task groups with multiple tasks spread across multiple quarters

    Task group  | Tasks | Start day           | End day
    2           | 4     | Mar/Jun/Sep/Dec  1  | Mar/Jun/Sep/Dec  5
    2           | 3     | Feb/May/Aug/Nov 20  | Feb/May/Aug/Nov 25
    1           | 2     | Feb/May/Aug/Nov 10  | Feb/May/Aug/Nov 20
    1           | 1     | Feb/May/Aug/Nov  1  | Feb/May/Aug/Nov  5

    Cycle should last from:
    Feb 1 - Mar 5
    May 1 - Jun 5
    Aug 1 - Sep 5
    Nov 1 - Dec 5
    """
    quarterly_wf = {
      "title": "quarterly thingy",
      "description": "start this many a time",
      "frequency": "quarterly",
      "task_groups": [{
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 4',
            "relative_start_day": 1,
            "relative_start_month": 3,
            "relative_end_day": 5,
            "relative_end_month": 3,
          }, {
            'title': 'quarterly task 3',
            "relative_start_day": 20,
            "relative_start_month": 2,
            "relative_end_day": 25,
            "relative_end_month": 2,
          }
        ],
        "task_group_objects": []
      }, {
        "title": "task group",
        "task_group_tasks": [
          {
            'title': 'quarterly task 2',
            "relative_start_day": 10,
            "relative_start_month": 2,
            "relative_end_day": 20,
            "relative_end_month": 2,
          }, {
            'title': 'quarterly task 1',
            "relative_start_day": 1,
            "relative_start_month": 2,
            "relative_end_day": 5,
            "relative_end_month": 2,
          }
        ],
        "task_group_objects": []
      }]
    }
    with freeze_time("2015-6-3 13:00:00"):  # Tuesday, 6/3/2015
      _, wf = self.generator.generate_workflow(quarterly_wf)
      _, awf = self.generator.activate_workflow(wf)

      active_wf = db.session.query(Workflow).filter(Workflow.id == wf.id).one()
      self.assertEqual(active_wf.status, "Active")
      self.assertEqual(active_wf.next_cycle_start_date, date(2015, 7, 31))

      cycle = db.session.query(Cycle).filter(
        Cycle.workflow_id == wf.id).one()
      self.assertEqual(cycle.start_date, date(2015, 5, 1))
      self.assertEqual(cycle.end_date, date(2015, 6, 5))

      dates = [
        ((2015, 7, 31), (2015, 9, 4), (2015, 10, 30)),
        ((2015, 10, 30), (2015, 12, 4), (2016, 2, 1)),
        ((2016, 2, 1), (2016, 3, 4), (2016, 4, 29)),
        ((2016, 4, 29), (2016, 6, 3), (2016, 8, 1))
      ]

      for csd, ced, ncsd in dates:
        _, cycle = self.generator.generate_cycle(wf)
        self.assertEqual(cycle.start_date, date(*csd))
        self.assertEqual(cycle.end_date, date(*ced))
        active_wf = db.session.query(Workflow).filter(
          Workflow.id == wf.id).one()
        self.assertEqual(active_wf.next_cycle_start_date, date(*ncsd))
