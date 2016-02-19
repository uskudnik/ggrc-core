# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

import abc
import datetime

from ggrc_workflows.services.workflow_cycle_calculator import google_holidays


@property
def NotImplementedProperty(self):
  raise NotImplementedError


@property
def NotImpementedMethod(self):
  raise NotImplementedError


class CycleCalculator(object):
  """Cycle calculation for all workflow frequencies with the exception of
  one-time workflows.

  Cycle calculator is an abstract class that implements all the operations
  needed by workflows, namely task_date_range, workflow_date_range and
  next_cycle_start_date.

  Each implementation of a class has to implement it's own
  relative_day_to_date method that calculates the real date based on
  the base_date provided to the method and taking into account the specifics
  of the frequency. relative_day_to_date SHOULD NOT adjust dates but
  should only convert them to datetime.date objects.

  Attributes:
    date_domain: Class implementation's domain in which values passed to it are
                 to be found
    time_delta: Class implementation's atomic unit by which
                addition/subtraction will take place during calculations.
    HOLIDAYS: Official holidays with the addition of several days that Google
              observes. See file google_holidays.py for details.
  """
  __metaclass__ = abc.ABCMeta

  date_domain = NotImplementedProperty
  time_delta = NotImplementedProperty

  HOLIDAYS = google_holidays.GoogleHolidays()

  @abc.abstractmethod
  def relative_day_to_date(self, relative_day, relative_month=None,
                           base_date=None):
    raise NotImplementedError("Converting from relative to real date"
                              "must be done on an instance.")

  @abc.abstractmethod
  def get_relative_start(task):
    raise NotImplementedError("Not implemented get_relative_start")

  @abc.abstractmethod
  def get_relative_end(task):
    raise NotImplementedError("Not implemented get_relative_end")

  def __init__(self, workflow, holidays=HOLIDAYS):
    """Initializes calculator based on the workflow and holidays.

    Generates a flat list of all the tasks in all task groups.

    Instances have to sort tasks based on relative
    start days (DD or MM/DD) and generate a dictionary self.reified_tasks
    where each key is task.id and values are dictionaries with
    relative_start, relative_end and calculated start_date and end_date
    values. Example:

      self.reified_tasks[task.id] = {
        'start_date': start_date,
        'end_date': end_date,
        'relative_start': task.relative_start_day,
        'relative_end': task.relative_end_day
      }

    Args:
      workflow: Workflow for which we are calculating
      holidays: List (or object supporting 'in' operation) with the list of
                holidays on which events won't happen.
    """
    self.workflow = workflow
    self.holidays = holidays
    self.tasks = [
        task for task_group in self.workflow.task_groups
        for task in task_group.task_group_tasks]

    self.sort_tasks()

  def sort_tasks(self):
    self.tasks.sort(key=lambda t: self.get_relative_start(t))

  def is_work_day(self, ddate):
    """Check whether specific ddate is workday or if it's a holiday/weekend.

    Args:
      ddate: datetime object
    Returns:
      Boolean: True if it's workday otherwise false.
    """
    return ddate.isoweekday() < 6 and ddate not in self.holidays

  def adjust_date(self, ddate):
    """Adjust date if it's not a work day.

    Calculates the first workday by going backwards by either subtracting
    appropriate number of days (if ddate is during weekend) or substracting
    by one day if it's a holiday. In case we still aren't on a workday we
    repeat the process recursively until we find the first workday.

    Args:
      date: datetime object
    Returns:
      datetime.date: First available workday.
    """
    # Short path
    if self.is_work_day(ddate):
      return ddate

    # Adjusting for weekends
    weekday = ddate.isoweekday()
    if weekday > 5:
      ddate = ddate - datetime.timedelta(days=(weekday - 5))

    # Adjusting for holidays
    if ddate in self.holidays:
      ddate = ddate - datetime.timedelta(days=1)

    # In case we still don't have a workday, repeat
    if not self.is_work_day(ddate):
      return self.adjust_date(ddate)
    return ddate

  def get_base_date(self, base_date=None):
    """Base date from which we will calculate must be less than or equal to the
    first tasks' relative day to ensure consistent calculation across different
    tasks."""
    if not base_date:
      base_date = datetime.date.today()

    first_day = base_date.day

    if self.tasks:
      _, first_day = self.get_first_task_relative()

    return datetime.date(
        base_date.year,
        base_date.month,
        min([first_day, base_date.day]))

  def get_first_task_relative(self):
    if self.tasks:
      task = self.tasks[0]
      first_relative_pair = self.get_relative_start(task)
      return first_relative_pair
    return None

  def get_last_task_relative(self):
    if self.tasks:
      task = self.tasks[-1]
      last_relative_pair = self.get_relative_end(task)
      return last_relative_pair
    return None

  @staticmethod
  def get_month_day_pair_from_relative(relative_pair):
    """Normalize relative pair to tuple"""
    # relative_pair = (relative_start_month, relative_start_day)
    if type(relative_pair) is tuple:
      rm, rd = relative_pair
    else:
      rd = relative_pair
      rm = None
    return rm, rd

  def workflow_date_range(self):
    """Calculates the min start date and max end date across all tasks.

    Returns:
      tuple({datetime.date, datetime.date}): First start date and
      last end date.
    """
    tasks_start_dates = [v['start_date'] for v in self.reified_tasks.values()]
    tasks_end_dates = [v['end_date'] for v in self.reified_tasks.values()]
    return min(tasks_start_dates), max(tasks_end_dates)

  def task_date_range(self, task, base_date=None):
    start_date, end_date = self.non_adjusted_task_date_range(task, base_date)
    return self.adjust_date(start_date), self.adjust_date(end_date)

  def non_adjusted_task_date_range(self, task,
                                   base_date=None, initialisation=False):
    """Calculates individual task's start and end date based on base_date.

    Taking base_date into account calculates individual task's start and
    end date with relative_day_to_date function provided by a specific
    implementation of a class.

    Args:
      task: Task object for which we are calculating start and end date
      base_date: Date based on which we convert from relative day to
                 real date.
    Returns:
      tuple({datetime.date, datetime.date}): Weekend and holiday
        adjusted start and end date.
    """
    if not base_date:
      base_date = datetime.date.today()

    start_date = self.relative_day_to_date(
        task.relative_start_day,
        relative_month=task.relative_start_month,
        base_date=base_date)

    end_date = self.relative_day_to_date(
        task.relative_end_day,
        relative_month=task.relative_end_month,
        base_date=base_date)

    # On initialisation `reified_tasks` haven't been initialised yet, making
    # this check unnecessary (and impossible).
    if not initialisation:
      min_rsm, min_rsd = self.get_month_day_pair_from_relative(
          self.get_first_task_relative())

      min_start = self.relative_day_to_date(
          relative_day=min_rsd, relative_month=min_rsm,
          base_date=base_date)

      # In certain cases (e.g. quarterly) the calculation of correct time unit
      # in which we operate can actually put start date of a specific task
      # BEFORE actual first task - in such case, we have to move start and end
      # dates one time unit forward.
      if start_date < min_start:
        start_date = start_date + self.time_delta
        end_date = end_date + self.time_delta

    # If the end_day is before start_day, end_date is overflowing
    # to next time unit.
    if end_date < start_date:
      end_date = end_date + self.time_delta
    return start_date, end_date

  def next_cycle_start_date(self, base_date=None):
    return self.adjust_date(self.non_adjusted_next_cycle_start_date(base_date))

  def non_adjusted_next_cycle_start_date(self, base_date=None):
    """Calculates workflow's next cycle start date.

    Calculates workflow's next cycle start date based based on the minimum
    start date of the tasks.

    Usually this is first element of self.tasks,

    Args:
      base_date: The start date of the time unit we are operating on.
    Returns:
      datetime.date: Adjusted date when the next cycle is going to be
                     generated.
    """
    today = datetime.date.today()
    if not base_date:
      base_date = today

    min_rsm, min_rsd = self.get_month_day_pair_from_relative(
        self.get_first_task_relative())
    max_rem, max_red = self.get_month_day_pair_from_relative(
        self.get_last_task_relative())

    min_start = self.relative_day_to_date(
        relative_day=min_rsd, relative_month=min_rsm,
        base_date=base_date)

    max_end = self.relative_day_to_date(
        relative_day=max_red, relative_month=max_rem,
        base_date=base_date)

    if max_end < min_start:
      max_end = max_end + self.time_delta

    # If we are calculating for a workflow who's first cycle is in the future
    # next start date is already calculated (min_start) and we don't have to
    # add to it, otherwise we have to add one time unit to the min_start.
    #
    # Example: We activate a weekly workflow on Monday, cycle start date
    # is on Tuesday, therefore next cycle start date is THIS Tuesday and
    # NOT NEXT Tuesday.
    #
    # This is only relevant when we activate workflow and not afterwards.
    if base_date == today:
      if min_start > today and max_end > today:
        base_date = base_date
      else:
        base_date = base_date + self.time_delta
    else:
      base_date = base_date + self.time_delta

    return self.relative_day_to_date(
        relative_day=min_rsd, relative_month=min_rsm,
        base_date=base_date)
