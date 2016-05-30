# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""A mixin for objects with statuses"""

from sqlalchemy.orm import validates

from werkzeug.exceptions import BadRequest


from ggrc import db


class Statusable(object):

  """Mixin with default labels for status field"""

  # pylint: disable=too-few-public-methods

  START_STATE = u"Not Started"
  PROGRESS_STATE = u"In Progress"
  DONE_STATE = u"Ready for Review"
  VERIFIED_STATE = u"Verified"
  FINAL_STATE = u"Completed"
  END_STATES = {VERIFIED_STATE, FINAL_STATE}

  NOT_DONE_STATES = {START_STATE, PROGRESS_STATE}
  DONE_STATES = {DONE_STATE} | END_STATES
  VALID_STATES = tuple(NOT_DONE_STATES | DONE_STATES)

  status = db.Column(
      db.Enum(*VALID_STATES),
      nullable=False,
      default=START_STATE)

  # State machine for all allowed transitions depending on whether verifiers
  # are defined or not.
  STATE_MACHINE = {
      False: {
          (None, START_STATE),
          (START_STATE, PROGRESS_STATE),
          (PROGRESS_STATE, FINAL_STATE),
          (FINAL_STATE, PROGRESS_STATE),
          (START_STATE, FINAL_STATE),
          (FINAL_STATE, START_STATE),
      },
      True: {
          (None, START_STATE),
          (START_STATE, PROGRESS_STATE),
          (PROGRESS_STATE, DONE_STATE),
          (DONE_STATE, PROGRESS_STATE),
          (START_STATE, DONE_STATE),
          (DONE_STATE, START_STATE),
          (DONE_STATE, VERIFIED_STATE),
          # All objects are in FINAL_STATE and not in VERIFIED_STATE
          (FINAL_STATE, DONE_STATE),
          (FINAL_STATE, PROGRESS_STATE),
          # The following is a hack for automatic conversion from
          # VERIFIED_STATE to FINAL_STATE
          (DONE_STATE, FINAL_STATE),
          # THe following is a hack for transition from FINAL_STATE to
          # PROGRESS_STATE
          (FINAL_STATE, PROGRESS_STATE)
      }
  }

  @validates("status")
  def validate_status(self, key, value):
    """Validate status transitions"""

    # Sqlalchemy only uses one validator per status (not neccessarily the
    # first) and ignores others. This enables cooperation between validators.
    if hasattr(super(Statusable, self), "validate_status"):
      value = super(Statusable, self).validate_status(key, value)

    if self.status == value:
      return value

    verifiers = any(True for _, roles in self.assignees
                    if "Verifier" in roles)

    valid_transitions = self.STATE_MACHINE[verifiers]

    if (self.status, value) in valid_transitions:
      return value

    message = ("Transition from \"{}\" to \"{}\" is not allowed.".format(
        self.status, value))

    raise BadRequest(message)
