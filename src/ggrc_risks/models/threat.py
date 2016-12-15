# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc import db
from ggrc.models.mixins import CustomAttributable, BusinessObject, Timeboxed
from ggrc.models.object_person import Personable
from ggrc.models.object_owner import Ownable
from ggrc.models.relationship import Relatable
from ggrc.models.mixins.snapshottable import SnapshottableChild
from ggrc.models.track_object_state import HasObjectState


class Threat(SnapshottableChild, HasObjectState, CustomAttributable,
             Personable, Relatable, Timeboxed, Ownable, BusinessObject,
             db.Model):

  __tablename__ = 'threats'

  _aliases = {
      "contact": {
          "display_name": "Contact",
          "filter_by": "_filter_by_contact",
      },
      "secondary_contact": None,
      "url": "Threat URL",
  }
