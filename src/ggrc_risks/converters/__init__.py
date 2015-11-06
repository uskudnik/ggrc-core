# Copyright (C) 2015 Reciprocity, Inc - All Rights Reserved
# Unauthorized use, copying, distribution, displaying, or public performance
# of this file, via any medium, is strictly prohibited. All information
# contained herein is proprietary and confidential and may not be shared
# with any third party without the express written consent of Reciprocity, Inc.
# Created By: anze@reciprocitylabs.com
# Maintained By: anze@reciprocitylabs.com


""" Module for handling import and export of all risk models """

from ggrc_risks import models

IMPORTABLE = {
    "risk": models.Risk,
    "threat": models.Threat,
}
