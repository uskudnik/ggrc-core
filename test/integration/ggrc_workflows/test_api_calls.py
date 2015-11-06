# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

import random
from integration.ggrc import TestCase

import os
from ggrc_workflows.models import Workflow, TaskGroup
from integration.ggrc.api_helper import Api
from nose.plugins.skip import SkipTest


if os.environ.get('TRAVIS', False):
  random.seed(1)  # so we can reproduce the tests if needed


class TestWorkflowsApiPost(TestCase):

  def setUp(self):
    TestCase.setUp(self)
    self.api = Api()

  def tearDown(self):
    pass

  def test_send_invalid_data(self):
    data = self.get_workflow_dict()
    del data["workflow"]["title"]
    del data["workflow"]["context"]
    response = self.api.post(Workflow, data)
    self.assert400(response)

  def test_create_one_time_workflows(self):
    data = self.get_workflow_dict()
    response = self.api.post(Workflow, data)
    self.assertEqual(response.status_code, 201)

  def test_create_weekly_workflows(self):
    data = self.get_workflow_dict()
    data["workflow"]["frequency"] = "weekly"
    data["workflow"]["title"] = "Weekly"
    response = self.api.post(Workflow, data)
    self.assertEqual(response.status_code, 201)

  def test_create_monthly_workflows(self):
    data = self.get_workflow_dict()
    data["workflow"]["frequency"] = "monthly"
    data["workflow"]["title"] = "Monthly"
    response = self.api.post(Workflow, data)
    self.assertEqual(response.status_code, 201)

  def test_create_quarterly_workflows(self):
    data = self.get_workflow_dict()
    data["workflow"]["frequency"] = "quarterly"
    data["workflow"]["title"] = "Quarterly"
    response = self.api.post(Workflow, data)
    self.assertEqual(response.status_code, 201)

  def test_create_annually_workflows(self):
    data = self.get_workflow_dict()
    data["workflow"]["frequency"] = "annually"
    data["workflow"]["title"] = "Annually"
    response = self.api.post(Workflow, data)
    self.assertEqual(response.status_code, 201)

  def test_create_task_group(self):
    wf_data = self.get_workflow_dict()
    wf_data["workflow"]["title"] = "Create_task_group"
    wf_response = self.api.post(Workflow, wf_data)

    wf = wf_response.json["workflow"]
    data = self.get_task_group_dict(wf)

    response = self.api.post(TaskGroup, data)
    self.assertEqual(response.status_code, 201)

  # TODO: Api should be able to handle invalid data
  @SkipTest
  def test_create_task_group_invalid_workflow_data(self):
    wf = {"id": -1, "context": {"id": -1}}
    data = self.get_task_group_dict(wf)

    response = self.api.post(TaskGroup, data)
    self.assert400(response)

  def get_workflow_dict(self):
    data = {
        "workflow": {
            "custom_attribute_definitions": [],
            "custom_attributes": {},
            "title": "One_time",
            "description": "",
            "frequency": "one_time",
            "notify_on_change": False,
            "task_group_title": "Task Group 1",
            "notify_custom_message": "",
            "owners": None,
            "context": None,
        }
    }
    return data

  def get_task_group_dict(self, wf):
    data = {
        "task_group": {
            "custom_attribute_definitions": [],
            "custom_attributes": {},
            "_transient": {},
            "contact": {
                "id": 1,
                "href": "/api/people/1",
                "type": "Person"
            },
            "workflow": {
                "id": wf["id"],
                "href": "/api/workflows/%d" % wf["id"],
                "type": "Workflow"
            },
            "context": {
                "id": wf["context"]["id"],
                "href": "/api/contexts/%d" % wf["context"]["id"],
                "type": "Context"
            },
            "modal_title": "Create Task Group",
            "title": "Create_task_group",
            "description": "",
        }
    }
    return data
