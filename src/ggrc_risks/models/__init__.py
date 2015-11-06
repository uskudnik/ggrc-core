# Copyright (C) 2015 Reciprocity, Inc - All Rights Reserved
# Unauthorized use, copying, distribution, displaying, or public performance
# of this file, via any medium, is strictly prohibited. All information
# contained herein is proprietary and confidential and may not be shared
# with any third party without the express written consent of Reciprocity, Inc.
# Created By: anze@reciprocitylabs.com
# Maintained By: anze@reciprocitylabs.com


from ggrc.models.all_models import register_model

from .risk import Risk
from .risk_object import RiskObject
from .threat import Threat

register_model(Risk)
register_model(RiskObject)
register_model(Threat)
