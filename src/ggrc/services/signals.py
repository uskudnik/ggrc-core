# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com


from blinker import Namespace

class Signals(object):
  signals = Namespace()

  custom_attribute_changed = signals.signal(
    'CA updated - after safe',
    """
    Indicates that a custom attributes was successfully saved to database.

      :obj: The model instance
      :value: New custom attribute value
      :service: The instance of Resource handling the CA PUT request
    """,
  )

