# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: mouli@meics.org
# Maintained By: miha@reciprocitylabs.com

from ggrc.services.common import Resource

from ggrc_workflows.models import (
    Workflow, Cycle, CycleTaskGroupObjectTask
)
from ggrc_workflows.services.common import Signals

from .data_handler import (
    get_cycle_data,
    get_workflow_data,
    get_task_group_task_data,
    get_cycle_task_data,
)

from .notification_handler import (
    handle_workflow_modify,
    handle_cycle_task_group_object_task_put,
    handle_cycle_created,
    handle_cycle_task_status_change,
)


def contributed_notifications():
  """ return handler functions for all object types
  """
  return {
      'Cycle': get_cycle_data,
      'Workflow': get_workflow_data,
      'TaskGroupTask': get_task_group_task_data,
      'CycleTaskGroupObjectTask': get_cycle_task_data,
  }


def register_listeners():

  @Resource.model_put.connect_via(Workflow)
  def workflow_put_listener(sender, obj=None, src=None, service=None):
    handle_workflow_modify(sender, obj, src, service)

  @Resource.model_put.connect_via(CycleTaskGroupObjectTask)
  def cycle_task_group_object_task_put_listener(
          sender, obj=None, src=None, service=None):
    handle_cycle_task_group_object_task_put(obj)

  @Resource.model_posted.connect_via(Cycle)
  def cycle_post_listener(sender, obj=None, src=None, service=None):
    handle_cycle_created(sender, obj, src, service, True)

  @Signals.status_change.connect_via(CycleTaskGroupObjectTask)
  def cycle_task_status_change_listener(
          sender, obj=None, new_status=None, old_status=None):
    handle_cycle_task_status_change(obj, new_status, old_status)

"""
All notifications handle the following structure:

  notifications = {
      "some@email.com": {
          "user": { user_info },

          # if notifications are forced for the given workflow
          "force_notifications": {
              notification.id :True/False
          }

          "cycle_starts_in": {
              workflow.id: {
                  "custom_message": ""
                  "title": ""
                  "workflow_url": "",
                  "workflow_owners":
                      { workflow_owner.id: workflow_owner_info, ...},
                  "start_date": MM/DD/YYYY
                  "fuzzy_start_date": "in X days/weeks ..."

                  "my_tasks" : # list of all tasks assigned to the user
                      { (task.id, object.id): { task_info, obj_info}, ... }

                  # list of all task groups assigned to the user, including
                  # tasks
                  "my_task_groups" :
                      { task_group.id:
                          { (task.id, object.id): { task_info, obj_info}, ... }
                      }

                  "workflow_tasks" : # list of all tasks in the workflow
                      { (task.id, object.id): { task_info, obj_info}, ... }
              }
              , ...
          }

          "cycle_start_failed": {
              workflow.id: {
                  "custom_message": ""
                  "title": ""
                  "workflow_url": "",
                  "workflow_owners":
                      { workflow_owner.id: workflow_owner_info, ...},
                  "start_date": MM/DD/YYYY
                  "fuzzy_start_date": "in X days/weeks ..."
              }
              , ...
          }

          "cycle_started": {
              cycle.id: {
                  # manually started cycles have instant notification
                  "manually": False

                  "custom_message": ""
                  "cycle_title": ""
                  "cycle_url": ""
                  "workflow_owners":
                      { workflow_owner.id: workflow_owner_info, ...},

                  "my_tasks" : # list of all tasks assigned to the user
                      { cycle_task.id: { task_info }, ...}

                  # list of all task groups assigned to the user, including
                  # tasks
                  "my_task_groups" :
                      { task_group.id:
                          { cycle_task.id: { task_info }, ... }, ...
                      }

                  "cycle_tasks" : # list of all tasks in the workflow
                      { cycle_task.id: { task_info }, ...}

              }
              , ...
          }

          "task_declined":
              { cycle_task.id: { task_info }, ...}

          "task_reassigned":
              { cycle_task.id: { task_info }, ...}

          "due_in": # tasks due in X days (x depends on notification type)
              { cycle_task.id: { task_info }, ...}

          "due_today":
              { cycle_task.id: { task_info }, ...}

          "all_tasks_completed": # only workflow owner gets this
              { workflow.id: { workflow_info }, ... }
      }
  }


Task and cycle_task have the following structure:

  task = {
      "title": title,
      "object_title": object title or "",
      "end_date": end date in MM/DD/YYYY format
      "fuzzy_due_in": "today" or "in 1 day"... "in 5 days", "in 1 week" etc.,
      "cycle_task_url" ""
  }

  """
