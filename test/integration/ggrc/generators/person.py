# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: ivan@reciprocitylabs.com
# Maintained By: ivan@reciprocitylabs.com

from integration.ggrc.api_helper import Api
from ggrc.models.person import Person
from ggrc_basic_permissions.models import Role, UserRole

import names

class PersonGenerator():
  roles = {
    'program_owner': 1,    # ProgramOwner
    'program_editor': 2,   # ProgramEditor
    'program_reader': 3,   # ProgramReader
    'reader': 5,           # Reader
    'editor': 6,           # Editor
    'program_creator': 7,  # ProgramCreator
    'admin': 8,            # Admin
  }


  def __init__(self, name=None, role=None):
    self.role = role
    self.api = Api()
    self.user = self.create_user(name)
    if self.role:
      self.permissions = self.set_role()

  def create_user(self, name):
    name = name if name else names.get_full_name()
    return self.api.post(Person, {'person': {
        'name': name,
        'email': '{}@reciprocitylabs.com'.format(name.replace(' ', '.').lower()),
        'context': None,
      }})

  def update_user(self):
    self.user = self.api.get(Person, self.get_id())
    return self.user

  def set_role(self):
    role_id = self.role if isinstance(self.role, (int, long, float, complex)) else self.roles[self.role]
    response = self.api.post(UserRole, {'user_role': {
        'context': None,
        'type': 'UserRole',
        'modified_by': {
          'href': '/api/people/1',
          'id': 1,
          'type': 'Person',
        },
        'person': {
          'context_id': None,
          'href': self.get_href(),
          'id': self.get_id(),
          'type': 'Person'
        },
        'role': {
          'href': '/api/user_roles/{}'.format(role_id),
          'type': 'Role',
          'id': role_id,
        },
      }})
    self.update_user()
    return response

  def get_id(self):
    return self.user.json['person']['id']

  def get_href(self):
    return '/api/people/{}'.format(self.user.json['person']['id'])

  def get_type(self):
    return self.user.json['person']['type']

  def get_name(self):
    return self.user.json['person']['name']

  def get_email(self):
    return self.user.json['person']['email']
