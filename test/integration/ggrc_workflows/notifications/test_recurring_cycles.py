# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

import random
from integration.ggrc import TestCase
from freezegun import freeze_time

import os
from mock import patch

from ggrc import notification
from ggrc.models import Person
from integration.ggrc_workflows.generator import WorkflowsGenerator
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator
from ggrc_workflows import views


if os.environ.get('TRAVIS', False):
  random.seed(1)  # so we can reproduce the tests if needed


class TestRecurringCycleNotifications(TestCase):

  def setUp(self):
    TestCase.setUp(self)
    self.api = Api()
    self.generator = WorkflowsGenerator()
    self.object_generator = ObjectGenerator()

    _, self.assignee = self.object_generator.generate_person(
        user_role="gGRC Admin")

    self.create_test_cases()

  def tearDown(self):
    pass

  def test_cycle_starts_in_less_than_X_days(self):

    with freeze_time("2015-02-01"):
      _, wf = self.generator.generate_workflow(self.quarterly_wf_1)
      response, wf = self.generator.activate_workflow(wf)

      self.assert200(response)

      assignee = Person.query.get(self.assignee.id)

    with freeze_time("2015-01-01"):
      _, notif_data = notification.get_todays_notifications()
      self.assertNotIn(assignee.email, notif_data)

    with freeze_time("2015-01-29"):
      _, notif_data = notification.get_todays_notifications()
      self.assertIn(assignee.email, notif_data)

    with freeze_time("2015-02-01"):
      _, notif_data = notification.get_todays_notifications()
      self.assertIn(assignee.email, notif_data)

  # TODO: this should mock google email api.
  @patch("ggrc.notification.email.send_email")
  def test_marking_sent_notifications(self, mail_mock):
    mail_mock.return_value = True

    with freeze_time("2015-02-01"):
      _, wf = self.generator.generate_workflow(self.quarterly_wf_1)
      response, wf = self.generator.activate_workflow(wf)

      self.assert200(response)

      assignee = Person.query.get(self.assignee.id)

    with freeze_time("2015-01-01"):
      _, notif_data = notification.get_todays_notifications()
      self.assertNotIn(assignee.email, notif_data)

    with freeze_time("2015-01-29"):
      views.send_todays_digest_notifications()
      _, notif_data = notification.get_todays_notifications()
      self.assertNotIn(assignee.email, notif_data)

    with freeze_time("2015-02-01"):
      _, notif_data = notification.get_todays_notifications()
      self.assertNotIn(assignee.email, notif_data)

  def create_test_cases(self):
    def person_dict(person_id):
      return {
          "href": "/api/people/%d" % person_id,
          "id": person_id,
          "type": "Person"
      }

    self.quarterly_wf_1 = {
        "title": "quarterly wf 1",
        "description": "",
        "owners": [person_dict(self.assignee.id)],
        "frequency": "quarterly",
        "notify_on_change": True,
        "task_groups": [{
            "title": "tg_1",
            "contact": person_dict(self.assignee.id),
            "task_group_tasks": [{
                "contact": person_dict(self.assignee.id),
                "description": self.generator.random_str(100),
                "relative_start_day": 5,
                "relative_start_month": 2,
                "relative_end_day": 25,
                "relative_end_month": 2,
            },
            ],
        },
        ]
    }

    self.all_workflows = [
        self.quarterly_wf_1,
    ]
