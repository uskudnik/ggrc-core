# Copyright (C) 2015 Reciprocity, Inc - All Rights Reserved
# Unauthorized use, copying, distribution, displaying, or public performance
# of this file, via any medium, is strictly prohibited. All information
# contained herein is proprietary and confidential and may not be shared
# with any third party without the express written consent of Reciprocity, Inc.
# Created By: anze@reciprocitylabs.com
# Maintained By: anze@reciprocitylabs.com

from ggrc import db
from ggrc.models.mixins import CustomAttributable, BusinessObject, Timeboxed
from ggrc.models.object_document import Documentable
from ggrc.models.object_person import Personable
from ggrc.models.object_owner import Ownable
from ggrc.models.relationship import Relatable
from ggrc.models.track_object_state import HasObjectState, track_state_for_class


class Threat(
    HasObjectState, CustomAttributable, Documentable, Personable,
    Relatable, Timeboxed, Ownable, BusinessObject, db.Model):
  __tablename__ = 'threats'

  _aliases = {
      "contact": {
          "display_name": "Contact",
          "filter_by": "_filter_by_contact",
      },
      "secondary_contact": None,
      "url": "Threat URL",
  }
