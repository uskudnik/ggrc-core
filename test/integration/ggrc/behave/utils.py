# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Provide commonly-used methods here.

Don't use ``@when``, ``@given``, etc. here, as it will raise
``behave.step_registry.AmbiguousStep``, since this module is included in
multiple steps/*.py modules.
"""
from __future__ import absolute_import

from ggrc.utils import as_json
import json
import datetime
from .factories import factory_for, FactoryStubMarker
import requests


def get_model(resource):
  import ggrc.models
  if isinstance(resource, Example):
    resource = resource.resource_type
  if isinstance(resource, (str, unicode)):
    if '.' in resource:
      # FIXME: Imports here shouldn't be needed, but extension module models
      #   aren't currently initialized (with ._inflector) before tests begin
      resource_module_path = '.'.join(resource.split(".")[:-1])
      resource_module = __import__(resource_module_path)
      resource = resource.split('.')[-1]
      resource = getattr(resource_module, resource)
    else:
      resource = ggrc.models.get_model(resource)
  return resource


def get_inflection(resource, inflection):
  model = get_model(resource)
  return unicode(getattr(model._inflector, inflection))


class Example(object):
  """An example resource for use in a behave scenario, by name."""
  def __init__(self, resource_type, value, response=None):
    self.resource_type = resource_type
    self.value = value
    self.response = response

  def get(self, attr):
    resource_root = get_inflection(self.resource_type, 'table_singular')
    return self.value.get(resource_root).get(attr)

  def set_embedded_val(self, attr, value):
    resource_root = get_inflection(self.resource_type, 'table_singular')
    self.value.get(resource_root)[attr] = value

  def set(self, attr, value):
    self.value[attr] = value

def set_property(obj, attr, value):
  if isinstance(obj, Example):
    obj.set(attr, value)
  else:
    setattr(obj, attr, value)


def handle_example_resource(context, resource_type):
  resource_factory = factory_for(resource_type)
  context.example_resource = resource_factory()

def handle_named_example_resource(
    step_context, resource_type, example_name, **kwargs):
  if type(resource_type) is str and '.' in resource_type:
    resource_type = get_model(resource_type)
  resource_factory = factory_for(resource_type)
  example = Example(resource_type, resource_factory(**kwargs))
  setattr(step_context, example_name, example)

def handle_get_resource_and_name_it(context, url, name):
  response = get_resource(context, url)
  assert response.status_code == 200
  setattr(context, '_response', response)
  setattr(context, name, response.json())

def get_resource(context, url, headers=None):
  headers = headers or {
      'Accept': 'application/json',
      'X-Requested-By': 'Reciprocity Behave Tests',
      }
  if hasattr(context, 'current_user_json'):
    headers['X-ggrc-user'] = context.current_user_json
  response = requests.get(
      context.base_url+url,
      headers=headers,
      cookies=getattr(context, 'cookies', {})
      )
  context.cookies = response.cookies
  return response

def put_resource(context, url, resource):
  headers={
      'Content-Type': 'application/json',
      'If-Match': resource.response.headers['Etag'],
      'If-Unmodified-Since': resource.response.headers['Last-Modified'],
      'X-Requested-By': 'Reciprocity Behave Tests',
      }
  if hasattr(context, 'current_user_json'):
    headers['X-ggrc-user'] = context.current_user_json
  data = as_json(resource.value)
  response = requests.put(
      context.base_url+url,
      data=data,
      headers=headers,
      cookies=getattr(context, 'cookies', {})
      )
  context.cookies = response.cookies
  return response

def handle_get_example_resource(context, name, expected_status=200):
  example = getattr(context, name)
  url = example.get('selfLink')
  response = get_resource(context, url)
  assert response.status_code == expected_status, \
      'Expected status code {0}, received {1}'\
        .format(expected_status, response.status_code)
  if expected_status == 200 or expected_status == 201:
    example = Example(
        example.resource_type, response.json(), response=response)
    setattr(context, name, example)

def handle_post_fails_with_status_and_content(context, name, expected_status, content):
  example = getattr(context, name)
  response = post_example(
      context, example.resource_type, example.value)
  assert response.status_code == expected_status, \
      'Expected status code {0}, received {1}'\
        .format(expected_status, response.status_code)
  assert response.text.find(content) != -1

def handle_post_named_example(context, name, expected_status=201):
  example = getattr(context, name)
  response = post_example(
      context, example.resource_type, example.value)
  assert response.status_code == expected_status, \
      'Expected status code {0}, received {1}'\
        .format(expected_status, response.status_code)
  if expected_status == 200 or expected_status == 201:
    example = Example(example.resource_type, response.json())
    setattr(context, name, example)
  return response

def post_to_endpoint(context, url, data):
  headers = {
      'Content-Type': 'application/json',
      'X-Requested-By': 'Reciprocity Behave Tests',
      }
  response = requests.post(
      context.base_url+url,
      data=data,
      headers=headers,
      allow_redirects=False,
      cookies=getattr(context, 'cookies', {}),
      )
  if response.status_code == 302:
    # deal with login redirect, expect noop
    headers={
        'Accept': 'text/html',
        'X-Requested-By': 'Reciprocity Behave Tests',
        }
    if hasattr(context, 'current_user_json'):
      headers['X-ggrc-user'] = context.current_user_json
    response = requests.get(
        response.headers['Location'],
        headers=headers,
        allow_redirects=False,
        )
    context.cookies = response.cookies
    response = requests.post(
        context.base_url+url,
        data=data,
        headers={
          'Content-Type': 'application/json',
          'X-Requested-By': 'Reciprocity Behave Tests',
          },
        cookies=context.cookies,
        )
  context.cookies = response.cookies
  return response

def post_example(context, resource_type, example, url=None, rbac_context=None):
  if rbac_context is None:
    rbac_context = example.get("context", None)

  # Find any required FactoryStubMarker and recurse to POST/create
  # required resources
  for attr, value in example.items():
    if isinstance(value, FactoryStubMarker):
      value_resource_type = value.class_.__name__

      # If the resource has subclasses, then it is abstract, so use one of
      #   its subclasses
      value_resource_subtypes = [
          manager.class_.__name__ for manager in
            value.class_._sa_class_manager.subclass_managers(True)]
      if len(value_resource_subtypes) > 0:
        value_resource_type = value_resource_subtypes[0]

      value_resource_factory = factory_for(value_resource_type)
      value_resource = value_resource_factory()
      value_response = post_example(
          context, value_resource_type, value_resource, rbac_context=rbac_context)
      # If not a successful creation, then it didn't create the object we need
      if value_response.status_code != 201:
        return value_response
      # Get the value of the first/only (key,value) pair
      #   (and just assume the root key is correct)
      value_data = value_response.json().items()[0][1]
      example[attr] = {
        'href': value_data["selfLink"],
        'id': value_data["id"],
        'type': value_resource_type
        }
  # Assign overriding `context`, if specified
  if rbac_context is not None:
    example["context"] = rbac_context

  resource_root = get_inflection(resource_type, 'table_singular')
  data = as_json({ resource_root: example })
  if url is None:
    url = get_service_endpoint_url_for_type(context, resource_type)
  return post_to_endpoint(context, url, data)

def get_service_endpoint_url_for_type(context, resource_type):
  endpoint_name = get_inflection(resource_type, 'model_singular')
  return get_service_endpoint_url(context, endpoint_name)

def get_service_endpoint_url(context, endpoint_name):
  """Return the URL for the `endpoint_name`. This assumes that there is a
  `service_description` in the `context` to ues to lookup the endpoint url.
  """
  return context.service_description.get(u'service_description')\
      .get(u'endpoints').get(unicode(endpoint_name)).get(u'href')

def handle_template_text(context, src):
  if '{{' in src:
    from jinja2 import Template
    template = Template(src)
    return template.render(context=context)
  return src

def check_for_resource_in_collection(
    context, collection_name, resource_name, expected):
  resource = getattr(context, resource_name)
  collection = getattr(context, collection_name)
  root = collection.keys()[0]
  table_plural = get_inflection(resource.resource_type, 'table_plural')
  entry_list = collection[root][table_plural]
  result_pairs = set(
      [(o.get(u'id'), o.get(u'selfLink') or o.get(u'href'))
        for o in entry_list])
  check_pair = (resource.get(u'id'), resource.get(u'selfLink'))
  if expected:
    assert check_pair in result_pairs, \
        'Expected to find {0} in results {1}'.format(
            check_pair, result_pairs)
  else:
    assert check_pair not in result_pairs, \
        'Expected not to find {0} in results {1}'.format(
            check_pair, result_pairs)
