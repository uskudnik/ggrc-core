# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

from ggrc_workflows.services.workflow_cycle_calculator import \
    annually_cycle_calculator
from ggrc_workflows.services.workflow_cycle_calculator import \
    monthly_cycle_calculator
from ggrc_workflows.services.workflow_cycle_calculator import \
    one_time_cycle_calculator
from ggrc_workflows.services.workflow_cycle_calculator import \
    quarterly_cycle_calculator
from ggrc_workflows.services.workflow_cycle_calculator import \
    weekly_cycle_calculator


def get_cycle_calculator(workflow, base_date=None):
  """Gets the cycle calculator based on the workflow's frequency.

  Args:
    workflow: Workflow object

  Returns:
    SomeCalculator(CycleCalculator): CycleCalculator's concrete implementation
  """
  calculators = {
      "one_time": one_time_cycle_calculator.OneTimeCycleCalculator,
      "weekly": weekly_cycle_calculator.WeeklyCycleCalculator,
      "monthly": monthly_cycle_calculator.MonthlyCycleCalculator,
      "quarterly": quarterly_cycle_calculator.QuarterlyCycleCalculator,
      "annually": annually_cycle_calculator.AnnuallyCycleCalculator
  }
  return calculators[workflow.frequency](workflow, base_date)
