# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from datetime import date, timedelta
import names
import random
import string

from ggrc import db
from ggrc.app import app
from ggrc.models import (
  Person, Policy, Control, Objective, Standard, System, NotificationConfig,
  CustomAttributeDefinition, Program, Audit, Assessment, Relationship
)
from ggrc.services.common import Resource
from ggrc_basic_permissions.models import UserRole, Role
from integration.ggrc.api_helper import Api


class Generator():

  def __init__(self):
    self.api = Api()
    self.resource = Resource()

  def random_str(self, length=8,
                 chars=string.ascii_uppercase + string.digits + "  _.-"):
    return ''.join(random.choice(chars) for _ in range(length))

  def random_date(self, start=date.today(), end=None):
    if not end or start > end:
      end = start + timedelta(days=7)
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())))

  def get_object(self, obj_class, obj_id):
    try:
      return db.session.query(obj_class).filter(obj_class.id == obj_id).one()
    except:
      return None

  def generate(self, obj_class, obj_name, data):
    response = self.api.post(obj_class, data)
    response_obj = None
    if response.json:
      response_obj = self.get_object(obj_class, response.json[obj_name]['id'])
    return response, response_obj

  def modify(self, obj, obj_name, data):
    obj_class = obj.__class__
    response = self.api.put(obj, data)
    response_obj = None
    if response.json:
      response_obj = self.get_object(obj_class, response.json[obj_name]['id'])
    return response, response_obj

  def obj_to_dict(self, obj, model_name=None):
    result = {}
    with app.app_context():
      result = self.resource.object_for_json(obj, model_name)
    return result


class ObjectGenerator(Generator):

  def generate_object(self, obj_class, obj_name, data={}):
    obj = obj_class(title=self.random_str())
    obj_dict = self.obj_to_dict(obj, obj_name)
    obj_dict[obj_name].update({"owners": [{
        "id": 1,
        "href": "/api/people/1",
        "type": "Person"
    }]})
    obj_dict[obj_name].update(data)
    return self.generate(obj_class, obj_name, obj_dict)

  def generate_policy(self, data={}):
    obj_name = "policy"
    default = {
        obj_name: {
            "title": "policy " + self.random_str(),
            "custom_attribute_definitions": [],
            "custom_attributes": {},
            "kind": "",
            "notes": "",
            "status": "Draft",
            "url": "",
            "end_date": "",
            "description": "",
            "context": None,
            "contact": {
                "id": 1,
                "href": "/api/people/1",
                "type": "Person"
            },
            "owners": [{
                "id": 1,
                "href": "/api/people/1",
                "type": "Person"
            }],
        }
    }
    default[obj_name].update(data)

    return self.generate(Policy, obj_name, default)

  def generate_relationship(self, source, destination, attr_type=None, attr=None):
    print "generate_relationship"
    print "source: ", source
    print "destination: ", destination
    data = {
      "relationship": {
        "source": {
          "id": source.id,
          "type": source.type
        },
        "destination": {
          "id": destination.id,
          "type": destination.type
        },
        "context": None},
    }
    if attr:
      data["relationship"].update({
        "attrs": {
          attr_type: attr
        }})
    # print "relationship payload: ", data
    return self.generate(Relationship, "relationship", data)

  def generate_user_roles(self, user_roles=None):
    if not user_roles:
      users_roles = [("creator", "Creator"), ("reader", "Reader"),
                     ("editor", "Editor"), ("admin", "gGRC Admin")]

    self.users = {}
    for (name, role) in users_roles:
      _, user = self.generate_person(
        data={"name": name}, user_role=role)
      self.users[name] = user
    return self.users

  def generate_program(self, person, data={}):
    print "generate program", person
    obj_name = "program"
    default = {
      obj_name: {
        "title": "program " + self.random_str(),
        "contact": {
          "id": person.id,
          "href": "/api/people/{}".format(person.id),
          "type": "Person"
        },
        "context": None,
        "description": "",
        "end_date": "",
        "kind": "Directive",
        "notes": "",
        "reference_url": "",
        "secondary_contact": None,
        "slug": "",
        "start_date": "",
        "status": "Draft",
        "url": "",
      }
    }

    default[obj_name].update(data)
    return self.generate(Program, obj_name, default)

  def generate_audit(self, program, person, data={}):
    obj_name = "audit"
    default = {
      obj_name: {
        "title": "audit " + self.random_str(),
        "contact": {
          "id": person.id,
          "href": "/api/people/{}".format(person.id),
          "type": "Person"
        },
        "context": {
          "id": program.context.id,
          "href": "/api/contexts/{}".format(program.context.id),
          "type": "Context"
        },
        "description":"",
        "modified_by_id":"150",
        "object_type":"Assessment",
        "program": {
          "id": program.id,
          "href": "/api/programs/{}".format(program.id),
          "type": "Program"
        },
        "slug":"",
        "status":"Planned",
      }
    }
    default[obj_name].update(data)
    return self.generate(Audit, obj_name, default)

  def generate_assessment(self,
                          program,
                          audit,
                          primary_contact,
                          assessment_object,
                          assessors, data={}):
    obj_name = "assessment"
    default = {
      obj_name: {
        "title": "assessment " + self.random_str(),
        "audit":{
          "id": audit.id,
          "href": "/api/audits/{}".format(audit.id),
          "type": "Audit"
        },
        "contact":{
          "id": primary_contact.id,
          "href": "/api/people/{}".format(primary_contact.id),
          "type": "Person"
        },
        "context":None,
        "description":"",
        "design":None,
        "notes":"",
        "object":{
          "id": assessment_object.id,
          "href": "/api/{}/{}".format(assessment_object.__tablename__, assessment_object.id),
          "type": "{}".format(assessment_object.type)
        },
        "operationally":None,
        "owners":[],
        "reference_url":"",
        "secondary_contact":None,
        "slug":"",
        "status":"Open",
        "test_plan":"",
        "url":"",
        "validate_assessor":True,
        "validate_creator":True,
      }
    }
    default[obj_name].update(data)
    assessment_response, assessment = self.generate(
      Assessment, obj_name, default)

    relationships_to_create = [(program,),(audit,)] + assessors

    created_relationships = []
    for rel in relationships_to_create:
      if len(rel) == 1:
        rel_obj = rel[0]
        res_rel = self.generate_relationship(assessment, rel_obj)
        created_relationships += [res_rel]
      else:
        rel_obj, rel_attr = rel
        res_rel = self.generate_relationship(assessment, rel_obj, "AssigneeType", rel_attr)
        created_relationships+= [res_rel]
    return (assessment_response, assessment), created_relationships

  def generate_user_role(self, person, role):
    data = {
        "user_role": {
            "context": None,
            "person": {
                "href": "/api/person/%d" % person.id,
                "id": person.id,
                "type": "Person"
            },
            "role": {
                "href": "/api/roles/%d" % role.id,
                "id": role.id,
                "type": "Role"
            }
        }
    }
    return self.generate(UserRole, "user_role", data)

  def generate_person(self, data={}, user_role=None):
    obj_name = 'person'
    name = names.get_full_name()
    default = {
        obj_name: {
            "context": None,
            "name": name,
            "email": "%s@test.com" % name.replace(" ", ".").lower(),
        }
    }
    default[obj_name].update(data)
    response, person = self.generate(Person, obj_name, default)

    if person and user_role:
      role = db.session.query(Role).filter(Role.name == user_role).first()
      self.generate_user_role(person, role)

    return response, person

  def generate_random_objects(self, count=5):
    random_objects = []
    classes = [Control, Objective, Standard, System]
    for _ in range(count):
      obj_class = random.choice(classes)
      obj_name = obj_class.__name__.lower()
      response, obj = self.generate_object(obj_class, obj_name)
      if obj:
        random_objects.append(obj)
    return random_objects

  def generate_random_people(self, count=5, **kwargs):
    random_people = []
    for _ in range(count):
      _, person = self.generate_person(**kwargs)
      if person:
        random_people.append(person)
    return random_people

  def generate_notification_setting(self, user_id, notif_type, enable_flag):
    obj_name = "notification_config"
    data = {
        obj_name: {
            "person_id": user_id,
            "notif_type": notif_type,
            "enable_flag": enable_flag,
            "context": None,
            "type": "NotificationConfig",
        }
    }
    return self.generate(NotificationConfig, obj_name, data)

  def generate_custom_attribute(self, definition_type, **kwargs):
    obj_name = "custom_attribute_definition"
    data = {
        obj_name: {
            "title": kwargs.get("title", self.random_str()),
            "custom_attribute_definitions": [],
            "custom_attributes": {},
            "definition_type": definition_type,
            "modal_title": kwargs.get("modal_title", self.random_str()),
            "attribute_type": kwargs.get("attribute_type", "Text"),
            "mandatory": kwargs.get("mandatory", False),
            "helptext": kwargs.get("helptext", False),
            "placeholder": kwargs.get("placeholder", False),
            "context": {"id": None},
            "multi_choice_options": kwargs.get("options", False),
        }
    }
    data[obj_name].update(kwargs)
    self.generate(CustomAttributeDefinition, obj_name, data)
