# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Handlers for request specific columns."""

from ggrc.converters.handlers import handlers
from ggrc.converters import errors
from ggrc.models import mixins_statusable


class StatusableColumnHandler(handlers.StatusColumnHandler):
  """Handler for request status."""

  def parse_item(self):
    """Parse raw_value into a valid request status if possible."""
    value = handlers.StatusColumnHandler.parse_item(self)
    obj = self.row_converter.obj

    if not mixins_statusable.Statusable.valid_import_transition(obj.status,
                                                                value):
      if (not obj.status and
         value not in mixins_statusable.Statusable.NOT_DONE_STATES):
        self.add_warning(
            errors.STATUSABLE_INVALID_STATE,
            object_type=obj.type)
        value = mixins_statusable.Statusable.PROGRESS_STATE
      else:
        self.add_warning(
            errors.STATUSABLE_INVALID_TRANSITION,
            object_type=obj.type, current_state=obj.status, new_state=value)
        value = mixins_statusable.Statusable.PROGRESS_STATE

    return value
