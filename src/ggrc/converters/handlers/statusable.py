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
    if value in models.Request.END_STATES:
      value = models.Request.PROGRESS_STATE
      self.add_warning(errors.REQUEST_INVALID_STATE)
    return value
