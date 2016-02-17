# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

import datetime
from dateutil import relativedelta

from ggrc_workflows.services.workflow_cycle_calculator import cycle_calculator


class MonthlyCycleCalculator(cycle_calculator.CycleCalculator):
  """CycleCalculator implementation for monthly workflows.

  Monthly workflows have a date domain from 1 to 31 and dates are adjusted
  to be in the same month if there are not enough days in the month.
  """
  time_delta = relativedelta.relativedelta(months=1)
  date_domain = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
                 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31}

  def __init__(self, workflow, base_date=None):
    super(MonthlyCycleCalculator, self).__init__(workflow)

    base_date = self.get_base_date(base_date)
    self.reified_tasks = {}
    for task in self.tasks:
      start_date, end_date = self.non_adjusted_task_date_range(
          task, base_date=base_date, initialisation=True)
      self.reified_tasks[task.id] = {
          'start_date': start_date,
          'end_date': end_date,
          'relative_start': task.relative_start_day,
          'relative_end': task.relative_end_day
      }

  @staticmethod
  def get_relative_start(task):
    return task.relative_start_day

  @staticmethod
  def get_relative_end(task):
    return task.relative_end_day

  def relative_day_to_date(self, relative_day, relative_month=None,
                           base_date=None):
    """Converts a monthly representation of a day into concrete date object.

    Monthly relative days are represented as days of the month; we calculate
    a concrete date by adding the difference between target relative day
    and day of the month of base_date. If month doesn't have enough days,
    the difference is subtracted from the date to ensure that the date is
    in the same month.

    If base_date is not provided it is assumed it's the start of the month.

    Example:
      If relative day is 31 and base_date (cycle start date) is
      5 (of January), we don't want need to do 5 + 31 but 5 + 26 to
      get back 31st of January.

      If however we are in February that only has 28 days we would get back
      3rd of March, therefore 3 days are subtracted to get back 28th
      of February.
    """
    today = datetime.date.today()
    relative_day = int(relative_day)
    if relative_day not in MonthlyCycleCalculator.date_domain:
      raise ValueError(
          "Monthly recurring cycles can only have relative day in 1-31 range.")

    if not base_date:
      base_date = datetime.date(today.year, today.month, 1)
    ddate = base_date + relativedelta.relativedelta(
        days=relative_day - base_date.day)

    # We want to go up to the end of the month and not over.
    if ddate.month != base_date.month:
      ddate = ddate - relativedelta.relativedelta(days=ddate.day)
    return ddate
