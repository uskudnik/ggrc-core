# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

"""Factories for basic permission models"""

from ggrc_basic_permissions import models

from integration.ggrc.models.factories import ModelFactory


class RoleFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.Role

  name = None
  permissions_json = None


class UserRoleFactory(ModelFactory):
  # pylint: disable=too-few-public-methods,missing-docstring,old-style-class
  # pylint: disable=no-init

  class Meta:
    model = models.UserRole
