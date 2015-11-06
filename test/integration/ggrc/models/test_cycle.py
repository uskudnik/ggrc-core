# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: brad@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from flask import Flask
from datetime import date, timedelta
from integration.ggrc import TestCase
#from ggrc_workflows import calc_start_date, calc_end_date
#def calc_end_date(frequency, _date, start_date):
from nose.plugins.skip import SkipTest

@SkipTest
class TestCycle(TestCase):

  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_dates_onetime(self):
    today = date.today()
    yesterday = today + timedelta(days=-1)
    #test 1: a weekday
    self.assertEqual(calc_start_date("one_time", today), today)
    self.assertEqual(calc_end_date("one_time", today, yesterday), today)
    #test 2: adjusting for the weekend
    saturday = date(2014, 7, 5)
    friday_before = date(2014, 7, 4)
    monday_after = date(2014, 7, 7)
    self.assertEqual(calc_start_date("one_time", saturday), monday_after)
    self.assertEqual(
      calc_end_date("one_time", saturday, friday_before),
      friday_before
      )


  def test_dates_monthly(self):
    _31daymonth = date(2014, 7, 31)
    start_of_july = date(2014, 7, 1)
    saturday = date(2014, 7, 5)
    friday_before = date(2014, 7, 4)
    monday_after = date(2014, 7, 7)
    next_month = date(2014, 8, 5)
    start_of_february = date(2014, 2, 1)
    end_of_february = date(2014, 2, 28)
    december_1 = date(2014, 12, 1)
    end_of_december = date(2014, 12, 31)
    january_2015 = date(2015, 1, 1)
    #test 1, adjusting for the weekend
    self.assertEqual(
      calc_start_date("monthly", saturday, start_of_july),
      monday_after
      )
    self.assertEqual(
      calc_end_date("monthly", saturday, friday_before),
      friday_before
      )
    #test 2, end date is next month if start day is later
    self.assertEqual(
      calc_end_date("monthly", saturday, monday_after),
      next_month
      )
    self.assertEqual(calc_end_date("monthly", saturday, saturday), next_month)
    #test 3, date is too large for current month, adjust to end of month
    self.assertEqual(
      calc_start_date("monthly", _31daymonth, start_of_february),
      end_of_february
      )
    self.assertEqual(
      calc_end_date("monthly", _31daymonth, start_of_february),
      end_of_february
      )
    #test 4, end date rolls over to next year if day of month is before
    # start date and start date is in december
    self.assertEqual(
      calc_end_date("monthly", december_1, end_of_december),
      january_2015
      )


  def test_dates_quarterly(self):
    _31daymonth = date(2014, 7, 31) #third quarter
    end_of_november = date(2014, 11, 30) #fourth quarter, month 2
    january_1 = date(2014, 1, 1) #first quarter
    end_of_january = date(2014, 1, 31)
    january_2015 = date(2015, 1, 30) #january 31, 2015 is a saturday
    end_of_february = date(2014, 2, 28)
    september_1 = date(2014, 9, 1) #third quarter, month 3
    end_of_october = date(2014, 10, 31) #fourth quarter, month 1
    #test 1: set appropriate first-quarter date from second-quarter base.
    self.assertEqual(
      calc_start_date("quarterly", _31daymonth, january_1),
      end_of_january
      )
    self.assertEqual(
      calc_end_date("quarterly", _31daymonth, january_1),
      end_of_january
      )
    #test 2: end-of-month adjustments
    self.assertEqual(
      calc_start_date("quarterly", end_of_november, january_1),
      end_of_february
      )
    self.assertEqual(
      calc_end_date("quarterly", end_of_november, january_1),
      end_of_february
      )
    #test 3: end date is calculated to later month (the next quarter) in some
    # cases. This is because the start date is usually the base date for end
    # date, and end date should always be after start date.
    # August 30, 2014 is a Saturday, so start date is September 1
    self.assertEqual(
      calc_start_date("quarterly", end_of_november, september_1),
     september_1
     )
    # November is month 2 of the 4th quarter, september is month 3 of the third
    # quarter, so here we should run over to the 4th quarter again and be the
    # fourth quarter
    self.assertEqual(
      calc_end_date("quarterly", end_of_october, end_of_november),
      january_2015
      )


  def test_dates_weekly(self):
    monday = date(2014, 7, 7)
    wednesday = date(2014, 7, 9)
    friday = date(2014, 7, 11)
    saturday = date(2014, 7, 12)
    next_monday = date(2014, 7, 14)
    #test 1a: start date is this week no matter when we start it.
    self.assertEqual(calc_start_date("weekly", monday, monday), monday)
    self.assertEqual(calc_start_date("weekly", monday, wednesday), monday)
    self.assertEqual(calc_start_date("weekly", wednesday, monday), wednesday)
    #test 1b: end date is always after start date, even the next week.
    self.assertEqual(calc_end_date("weekly", monday, monday), next_monday)
    self.assertEqual(calc_end_date("weekly", monday, wednesday), next_monday)
    self.assertEqual(calc_end_date("weekly", wednesday, monday), wednesday)
    #test 2: weekends are adjusted correctly
    self.assertEqual(calc_start_date("weekly", saturday, saturday), next_monday)
    self.assertEqual(calc_end_date("weekly", saturday, wednesday), friday)


  def test_dates_annually(self):
    _31daymonth = date(2014, 7, 31)
    january_1 = date(2014, 1, 1)
    january_2015 = date(2015, 1, 1)
    july_2015 = date(2015, 7, 31)
    #test 1: set appropriate date for start and end
    self.assertEqual(
      calc_start_date("annually", _31daymonth, january_1),
      _31daymonth
      )
    self.assertEqual(
      calc_end_date("annually", _31daymonth, january_1),
      _31daymonth
      )
    self.assertEqual(
      calc_end_date("annually", january_1, _31daymonth),
      january_2015
      )
    #test 2: different year than base
    self.assertEqual(
      calc_start_date("annually", _31daymonth, january_2015),
      july_2015
      )
    self.assertEqual(
      calc_end_date("annually", _31daymonth, january_2015),
      july_2015
      )
