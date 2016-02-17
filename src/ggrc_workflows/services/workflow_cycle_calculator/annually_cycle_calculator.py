# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

import datetime
from dateutil import relativedelta

from ggrc_workflows.services.workflow_cycle_calculator import cycle_calculator


class AnnuallyCycleCalculator(cycle_calculator.CycleCalculator):
  """CycleCalculator implementation for annual workflows.

  Month domain is 1-12, date domain is 1-31.
  """

  time_delta = relativedelta.relativedelta(years=1)
  date_domain = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
                 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31}
  month_domain = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}

  def __init__(self, workflow, base_date=None):
    super(AnnuallyCycleCalculator, self).__init__(workflow)

    base_date = self.get_base_date(base_date)
    self.reified_tasks = {}
    for task in self.tasks:
      start_date, end_date = self.non_adjusted_task_date_range(
          task, base_date, initialisation=True)
      self.reified_tasks[task.id] = {
          'start_date': start_date,
          'end_date': end_date,
          'relative_start': (task.relative_start_month,
                             task.relative_start_day),
          'relative_end': (task.relative_end_month, task.relative_end_day)
      }

  @staticmethod
  def get_relative_start(task):
    return (task.relative_start_month, task.relative_start_day)

  @staticmethod
  def get_relative_end(task):
    return (task.relative_end_month, task.relative_end_day)

  def relative_day_to_date(self, relative_day, relative_month=None,
                           base_date=None):
    """Converts an annual relative day representation to concrete date object

    First we ensure that we have both relative_day and relative_month or,
    alternatively, that relative_day carries month information as well.

    While task_date_range calls with explicit relative_month, reified_tasks
    stores relative days as MM/DD and we must first convert these values so
    that it can sort and get min and max values for tasks.

    Afterwards we repeat the math similar to monthly cycle calculator and
    ensure that the day is not overflowing to the next month.
    """

    relative_day = int(relative_day)
    relative_month = int(relative_month)

    if relative_day not in AnnuallyCycleCalculator.date_domain:
      raise ValueError

    if relative_month not in AnnuallyCycleCalculator.month_domain:
      raise ValueError

    base_date = self.get_base_date(base_date)

    start_month = datetime.date(base_date.year, relative_month, 1)
    ddate = start_month + relativedelta.relativedelta(days=relative_day - 1)

    # We want to go up to the end of the month and not over
    if ddate.month != start_month.month:
      ddate = ddate - relativedelta.relativedelta(days=ddate.day)
    return ddate
