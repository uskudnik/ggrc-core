# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

import factory
import random
from datetime import date


from ggrc_workflows import models
from integration.ggrc.models.factories import ModelFactory
from integration.ggrc.models.factories import TitledFactory


class WorkflowFactory(ModelFactory, TitledFactory):

  class Meta:
    model = models.Workflow

  frequency = "one_time"


class TaskGroupFactory(ModelFactory, TitledFactory):

  class Meta:
    model = models.TaskGroup

  workflow = factory.SubFactory(WorkflowFactory)


class TaskGroupObjectFactory(ModelFactory):

  class Meta:
    model = models.TaskGroupObject

  task_group = factory.SubFactory(TaskGroupFactory)
  object_id = 0
  object_type = ""


class TaskGroupTaskFactory(ModelFactory, TitledFactory):

  class Meta:
    model = models.TaskGroupTask

  task_group = factory.SubFactory(TaskGroupFactory)
  task_type = "text"


class CycleFactory(ModelFactory, TitledFactory):

  class Meta:
    model = models.Cycle

  workflow = factory.SubFactory(WorkflowFactory)


class CycleTaskGroupFactory(ModelFactory, TitledFactory):

  class Meta:
    model = models.CycleTaskGroup

  cycle = factory.SubFactory(CycleFactory)


class CycleTaskFactory(ModelFactory, TitledFactory):

  class Meta:
    model = models.CycleTaskGroupObjectTask

  cycle = factory.SubFactory(CycleFactory)
  cycle_task_group = factory.SubFactory(CycleTaskGroupFactory)
  task_group_task = factory.SubFactory(TaskGroupTaskFactory)
  task_type = "text"
  start_date = date(2015, 12, 4)
  end_date = date(2015, 12, 27)


class CycleTaskObjectFactory(ModelFactory, TitledFactory):

  class Meta:
    model = models.CycleTaskGroupObject

  task_group_object= factory.SubFactory(TaskGroupObjectFactory)
  cycle_task_group = factory.SubFactory(CycleTaskGroupFactory)
  cycle = factory.SubFactory(CycleFactory)
  object_id = 0
  object_type = "test"


