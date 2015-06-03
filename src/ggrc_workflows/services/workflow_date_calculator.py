# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: laran@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from datetime import date, timedelta
from monthdelta import monthdelta
from calendar import monthrange

'''
All dates are calculated raw. They are not adjusted for holidays or workdays.
Use WorkflowDateCalculator.nearest_work_day() to get a date adjusted for
weekends & holidays.

# !Note! The dates returned by these basic methods do not adjust for holidays or weekends.
# !Note! Adjusting for holidays and weekends is way too hard to test effectively, and, because
# !Note! of the fact that the dates are calculated relatively from one another, adjusting them
# !Note! as they're being calculated makes it impossible to do things like jump ahead to future
# !Note! cycles or jump back to previous ones.
# !Note! So adjust for weekends & holidays, calculate the final start/end date that you want.
# !Note! Once you have the date, adjust that final date by calling WorkflowDateCalculator.nearest_workday(your_date)
# !Note! to adjust the final date.

The calculator works in two ways:

  1) Create an instance, giving it a workflow, and it call instance methods. This is a bit more object-oriented:

      # Get the boundary dates for a cycle
      start_date = calculator.nearest_start_date_after_basedate(basedate)
      end_date   = calculator.nearest_end_date_after_start_date(start_date)

      # Calculate prior cycle periods from a basedate
      prior_cycle_start_date = calculator.previous_cycle_start_date_before_basedate(basedate)
      prior_cycle_end_date   = calculator.nearest_end_date_after_start_date(prior_cycle_start_date)

      # For convenience, calculate subsequent cycle start date
      next_cycle_start_date = calculator.next_cycle_start_date_after_basedate(basedate)
      # This is effectively the same as doing this:
      next_cycle_start_date = calculator.nearest_start_date_after_basedate(start_date + timedelta(days=1))

  2) Use the static methods which calculate cycle boundaries given dates. This is a bit more utilitarian, and
    is valuable in certain cases, such as when making calculations directly with TaskGroupTasks, where you may or may
    not have the workflow in scope.

      # Get the boundary dates for a cycle
      # !Incidentally, for weekly cycles the relative_{start|end}_month can be None
      # !Notice that these methods below use relative month+day instead of date values.
      start_date = WorkflowDateCalculator.nearest_start_date_after_basedate_from_dates(\
        basedate, frequency, relative_start_month, relative_start_day)
      end_date   = WorkflowDateCalculator.nearest_end_date_after_start_date_from_dates(\
        frequency, start_date, end_month, end_day)
      prior_cycle_start_date = WorkflowDateCalculator.previous_cycle_start_date_before_basedate_from_dates(
        basedate, frequency, relative_start_month, relative_start_day)
      prior_cycle_end_date   = WorkflowDateCalculator.nearest_end_date_after_start_date_from_dates(\
        basedate, frequency, prior_cycle_start_date.month, prior_cycle_start_date.day)
      next_cycle_start_date = WorkflowDateCalculator.next_cycle_start_date_after_basedate_from_dates(\
        basedate, frequency, relative_start_month, relative_start_day
      # Again, this is equivalent to this
      next_cycle_start_date = WorkflowDateCalculator.nearest_start_date_after_basedate(\
        basedate, frequency, relative_start_month, relative_start_day+1)

Again, the dates returned by all of the methods above do not adjust for weekends or holidays.

To adjust a date for weekends & holidays you have three (static) methods to use:

  # Know that direction = 1 means forward, direction = -1 means backward
  WorkflowDateCalculator.nearest_work_day(your_date, direction)

  # You can also use the slightly more obvious methods which hide the complexity of understanding what the direction
  # values mean.
  WorkflowDateCalculator.adjust_start_date(frequency, your_start_date)
  WorkflowDateCalculator.adjust_end_date(frequency, your_end_date)

One thing to note is:
 TaskGroupTasks for one_time workflows store their date values as start_date & end_date.
 TaskGroupTasks for non-one_time worklows store their date values as
 relative_start_{month|day} & relative_end_{month|day}

 The logic and tests have taken this into account.

'''

class WorkflowDateCalculator(object):
  def __init__(self, workflow=None):
    self.workflow = workflow

  '''
  direction = 1  indicates FORWARD
  direction = -1 indicates BACKWARD
  '''
  @staticmethod
  def nearest_work_day(date_, direction, frequency):
    if date_ is None:
      return None

    year = date.today().year
    holidays = [
        date(year=year, month=1, day=1),   # Jan 01 New Year's Day
        date(year=year, month=1, day=19),  # Jan 19 Martin Luther King Day
        date(year=year, month=2, day=16),  # Feb 16 President's Day
        date(year=year, month=5, day=25),  # May 25 Memorial Day
        date(year=year, month=7, day=2),   # Jul 02 Independence Day Holiday
        date(year=year, month=7, day=3),   # Jul 03 Independence Day Eve
        date(year=year, month=9, day=7),   # Sep 07 Labor Day
        date(year=year, month=11, day=26), # Nov 26 Thanksgiving Day
        date(year=year, month=11, day=27), # Nov 27 Thanksgiving Day 2
        date(year=year, month=12, day=23), # Dec 23 Christmas Holiday
        date(year=year, month=12, day=24), # Dec 24 Christmas Eve
        date(year=year, month=12, day=25), # Dec 25 Christmas Day
        date(year=year, month=12, day=31), # Dec 31 New Year's Eve
    ]

    if frequency != "one_time":
      holidays = []
      while date_.isoweekday() > 5 or date_ in holidays:
        date_ = date_ + timedelta(direction)
    return date_

  @staticmethod
  def adjust_start_date(frequency, start_date):
    return WorkflowDateCalculator.nearest_work_day(start_date, 1, frequency)

  @staticmethod
  def adjust_end_date(frequency, end_date):
    return WorkflowDateCalculator.nearest_work_day(end_date, -1, frequency)

  def nearest_start_date_after_basedate(self, basedate):
    frequency = self.workflow.frequency

    min_start_year = self._min_start_year_from_tasks()
    min_relative_start_day = self._min_relative_start_day_from_tasks()
    min_relative_start_month = self._min_relative_start_month_from_tasks()

    # Both min_relative_start values will be None when the workflow has no tasks.
    if min_relative_start_day is None and min_relative_start_month is None:
      return None

    return WorkflowDateCalculator.nearest_start_date_after_basedate_from_dates(
      basedate, frequency, min_relative_start_month, min_relative_start_day, min_start_year)

  @staticmethod
  def nearest_start_date_after_basedate_from_dates(
      basedate, frequency, relative_start_month, relative_start_day, start_year=None):

    if basedate is None:
      return None

    if "one_time" == frequency:
      return date(year=start_year, month=relative_start_month, day=relative_start_day)
    elif "weekly" == frequency:
      if relative_start_day == basedate.isoweekday():
        return basedate
      elif relative_start_day > basedate.isoweekday():
        day_delta = relative_start_day - basedate.isoweekday()
        return basedate + timedelta(days=day_delta)
      elif relative_start_day < basedate.isoweekday():
        day_delta = basedate.isoweekday() - relative_start_day
        return basedate + timedelta(days=7 - day_delta)
    elif "monthly" == frequency:
      if relative_start_day == basedate.day:
        return basedate
      elif relative_start_day > basedate.day:
        day_delta = relative_start_day - basedate.day
        return basedate + timedelta(days=day_delta)
      elif relative_start_day < basedate.day:
        start_date = basedate
        while start_date.day > relative_start_day:
          start_date = start_date + timedelta(days=-1)
        return start_date + monthdelta(1)
    elif "quarterly" == frequency:
      base_quarter_month = basedate.month % 3
      # We want 1-3 indexing instead of 0-2
      if base_quarter_month == 0:
        base_quarter_month = 3
      min_relative_start_quarter_month = relative_start_month

      if min_relative_start_quarter_month == base_quarter_month:
        if relative_start_day == basedate.day:
          return basedate  # Start today
        elif relative_start_day < basedate.day:
          start_date = date(basedate.year, basedate.month, basedate.day)
          start_date = start_date + monthdelta(3)
          day_delta = -1 * (basedate.day - relative_start_day)
          start_date = start_date + timedelta(days=day_delta)
          return start_date
        else:
          return date(year=basedate.year, month=basedate.month, day=relative_start_day)
      elif min_relative_start_quarter_month < base_quarter_month:
        start_date = date(
          year=basedate.year,
          month=basedate.month,
          day=relative_start_day
        ) + monthdelta(1)
        tmp_start_date = start_date
        tmp_quarter_month = tmp_start_date.month % 3
        if tmp_quarter_month == 0:
          tmp_quarter_month = 3
        month_counter = 1
        while tmp_quarter_month < min_relative_start_quarter_month:
          # Use start_date + monthdelta instead of adding 1 month at a time
          # with monthdelta(1) because monthdelta(1) adjusts the end date of
          # the month for the number of days in the month.
          tmp_start_date = start_date + monthdelta(month_counter)
          tmp_quarter_month = tmp_start_date.month % 3
          if tmp_quarter_month == 0:
            tmp_quarter_month = 3
        return tmp_start_date
      else:  # min_relative_start_quarter_month > base_quarter_month: Walk forward to a valid month
        delta = abs(relative_start_month - base_quarter_month)
        start_date = basedate + monthdelta(int(delta))  # int cast because delta is a long
        return date(
            year=start_date.year,
            month=start_date.month,
            day=relative_start_day  # we are hoping the user didn't enter an invalid start_date (this pattern is used throughout this file)
        )
    elif "annually" == frequency:
      if basedate.month == relative_start_month:
        if basedate.day == relative_start_day:
          return basedate
        elif basedate.day > relative_start_day:
          return date(year=basedate.year, month=relative_start_month, day=relative_start_day) + monthdelta(12)
        elif basedate.day < relative_start_day:
          return date(year=basedate.year, month=relative_start_month, day=relative_start_day)
      elif basedate.month > relative_start_month:
        return date(year=basedate.year, month=relative_start_month, day=relative_start_day) + monthdelta(12)
      else:
        return date(year=basedate.year, month=relative_start_month, day=relative_start_day)
    else:
      pass

  def nearest_end_date_after_start_date(self, start_date):
    frequency = self.workflow.frequency

    #TODO: fix the entire logic here. months and days can't be calculated separately
    max_end_year = self._max_end_year_from_tasks()
    max_relative_end_day = self._max_relative_end_day_from_tasks()
    max_relative_end_month = self._max_relative_end_month_from_tasks()
    return WorkflowDateCalculator.nearest_end_date_after_start_date_from_dates(
      frequency, start_date, max_relative_end_month, max_relative_end_day, max_end_year)

  @staticmethod
  def nearest_end_date_after_start_date_from_dates(frequency, start_date, end_month, end_day, end_year=None):
    # Handle no start_date, which will happen when the workflow has no tasks.
    if start_date is None:
      return None

    if "one_time" == frequency:
      end_day = min(monthrange(start_date.year, end_month)[1], end_day)
      end_date = date(year=end_year, month=end_month, day=end_day)
      if end_date < start_date:
          raise ValueError("End date cannot be before start date.")
      return end_date
    elif "weekly" == frequency:
      if end_day == start_date.isoweekday():
        return start_date
      elif end_day < start_date.isoweekday():
        return start_date + timedelta(days=end_day + (7 - start_date.isoweekday()))
      else:
        return start_date + timedelta(days=(end_day - start_date.isoweekday()))
    elif "monthly" == frequency:
      if end_day == start_date.day:
        return start_date
      elif end_day < start_date.day:
        end_date = start_date + monthdelta(1)
        while end_date.day > end_day:
          end_date = end_date + timedelta(days=-1)
        return end_date
      else:
        return start_date + timedelta(days=(end_day - start_date.day))
    elif "quarterly" == frequency:
      start_quarter_month = start_date.month % 3
      # Offset month because we want 1-based indexing, not 0-based
      if start_quarter_month == 0:
        start_quarter_month = 3
      if start_quarter_month == end_month:
        if start_date.day == end_day:
          return start_date
        elif start_date.day < end_day:
          return date(year=start_date.year, month=start_date.month, day=end_day)
        else:
          _end_month = start_date.month + 3
          _year = start_date.year
          if _end_month > 12:
            _year += _end_month / 12
            _end_month = (_end_month % 12)
          return date(year=_year, month=_end_month, day=end_day)
      elif start_quarter_month < end_month:
        return date(
          year=start_date.year,
          month=start_date.month + (end_month - start_quarter_month),
          day=end_day)
      else:
        end_date = date(
          year=start_date.year,
          month=start_date.month,
          day=end_day
        ) + monthdelta(1)
        tmp_end_date = end_date
        tmp_quarter_month = tmp_end_date.month % 3
        if tmp_quarter_month == 0:
          tmp_quarter_month = 3
        month_counter = 1
        # Can't use less_than operator here because of the looping
        # around quarters.
        while tmp_quarter_month != end_month:
          # Use start_date + monthdelta instead of adding 1 month at a time
          # with monthdelta(1) because monthdelta(1) adjusts the end date of
          # the month for the number of days in the month.
          tmp_end_date = end_date + monthdelta(month_counter)
          tmp_quarter_month = tmp_end_date.month % 3
          if tmp_quarter_month == 0:
            tmp_quarter_month = 3
        return tmp_end_date
    elif "annually" == frequency:
      if start_date.month == end_month:
        if start_date.day == end_day:
          return start_date
        elif start_date.day < end_day:
          return date(year=start_date.year, month=start_date.month, day=end_day)
        else:
          return date(year=start_date.year, month=start_date.month, day=end_day) + monthdelta(12)
      elif start_date.month < end_month:
        return date(year=start_date.year, month=end_month, day=end_day)
      else:
        return date(year=start_date.year, month=end_month, day=end_day) + monthdelta(12)
    else:
      pass

  @staticmethod
  def next_cycle_start_date_after_start_date(start_date, frequency):
    if start_date is None:
      return None

    if "one_time" == frequency:
      return start_date
    elif "weekly" == frequency:
      return start_date + timedelta(days=7)
    elif "monthly" == frequency:
      return start_date + monthdelta(1)
    elif "quarterly" == frequency:
      return start_date + monthdelta(3)
    elif "annually" == frequency:
      return start_date + monthdelta(12)
    else:
      pass

  @staticmethod
  def next_cycle_start_date_after_basedate_from_dates(
      basedate, frequency, relative_start_month, relative_start_day):
    start_date = WorkflowDateCalculator.\
      nearest_start_date_after_basedate_from_dates(
      basedate, frequency, relative_start_month, relative_start_day)
    return WorkflowDateCalculator.next_cycle_start_date_after_start_date(start_date, frequency)

  def next_cycle_start_date_after_basedate(self, basedate):
    start_date = self.nearest_start_date_after_basedate(basedate)
    frequency = self.workflow.frequency
    return WorkflowDateCalculator.\
      next_cycle_start_date_after_start_date(start_date, frequency)

  @staticmethod
  def previous_cycle_start_date_before_basedate_from_dates(
      basedate, frequency, relative_start_month, relative_start_day):
    start_date = WorkflowDateCalculator.\
      nearest_start_date_after_basedate_from_dates(
      basedate, frequency, relative_start_month, relative_start_day)
    return WorkflowDateCalculator.\
      previous_cycle_start_date(start_date, frequency)

  @staticmethod
  def previous_cycle_start_date(start_date, frequency):
    if start_date is None:
      return None

    if "one_time" == frequency:
      return start_date
    elif "weekly" == frequency:
      return start_date + timedelta(days=-7)
    elif "monthly" == frequency:
      return start_date + monthdelta(-1)
    elif "quarterly" == frequency:
      return start_date + monthdelta(-3)
    elif "annually" == frequency:
      return start_date + monthdelta(-12)
    else:
      pass

  @staticmethod
  def relative_month_from_date(_date, frequency):
    if "one_time" == frequency:
      return _date.month
    elif "weekly" == frequency:
      return None
    elif "monthly" == frequency:
      return None
    elif "quarterly" == frequency:
      month = _date.month % 3
      if month == 0:
        month = 3
      return month
    elif "annually" == frequency:
      return _date.month
    else:
      pass

  @staticmethod
  def relative_day_from_date(_date, frequency):
    if "one_time" == frequency:
      return _date.day
    elif "weekly" == frequency:
      return _date.isoweekday()
    elif "monthly" == frequency:
      return _date.day
    elif "quarterly" == frequency:
      return _date.day
    elif "annually" == frequency:
      return _date.day
    else:
      pass

  def previous_cycle_start_date_before_basedate(self, basedate):
    start_date = self.nearest_start_date_after_basedate(basedate)
    frequency = self.workflow.frequency
    return WorkflowDateCalculator.\
      previous_cycle_start_date(start_date, frequency)

  def _min_start_year_from_tasks(self):
    if self.workflow.frequency != "one_time":
      return None

    min_start_year = None
    for tg in self.workflow.task_groups:
      for t in tg.task_group_tasks:
        start_year = t.start_date.year
        if min_start_year is None or start_year < min_start_year:
          min_start_year = start_year
    return min_start_year

  def _max_end_year_from_tasks(self):
    if self.workflow.frequency != "one_time":
      return None

    max_end_year = None
    for tg in self.workflow.task_groups:
      for t in tg.task_group_tasks:
        end_year = t.end_date.year
        if max_end_year is None or end_year < max_end_year:
          max_end_year = end_year
    return max_end_year

  def _min_relative_start_month_from_tasks(self):
    min_start_month = None
    for tg in self.workflow.task_groups:
      for t in tg.task_group_tasks:
        if "one_time" == self.workflow.frequency:
          relative_start_month = WorkflowDateCalculator.\
            relative_month_from_date(t.start_date, self.workflow.frequency)
        else:
          relative_start_month = t.relative_start_month
        if min_start_month is None or relative_start_month < min_start_month:
          min_start_month = relative_start_month
    return min_start_month

  def _min_relative_start_day_from_tasks(self):
    min_start_day = None
    for tg in self.workflow.task_groups:
      for t in tg.task_group_tasks:
        if "one_time" == self.workflow.frequency:
          relative_start_day = WorkflowDateCalculator.\
            relative_day_from_date(t.start_date, self.workflow.frequency)
        else:
          relative_start_day = t.relative_start_day
        if min_start_day is None or relative_start_day < min_start_day:
          min_start_day = relative_start_day
    return min_start_day

  def _max_relative_end_day_from_tasks(self):
    max_end_day = None
    for tg in self.workflow.task_groups:
      for t in tg.task_group_tasks:
        if "one_time" == self.workflow.frequency:
          relative_end_day = WorkflowDateCalculator.\
            relative_day_from_date(t.end_date, self.workflow.frequency)
        else:
          relative_end_day = t.relative_end_day
        if max_end_day is None or relative_end_day > max_end_day:
          max_end_day = relative_end_day
    return max_end_day

  def _max_relative_end_month_from_tasks(self):
    max_end_month = None
    for tg in self.workflow.task_groups:
      for t in tg.task_group_tasks:
        if "one_time" == self.workflow.frequency:
          relative_end_month = WorkflowDateCalculator.\
            relative_month_from_date(t.end_date, self.workflow.frequency)
        else:
          relative_end_month = t.relative_end_month
        if max_end_month is None or relative_end_month > max_end_month:
          max_end_month = relative_end_month
    return max_end_month
