# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

import json
from flask import request, current_app
from flask.views import MethodView

from ggrc import services

"""RESTful service discovery API for gGRC services."""

class ServiceDescription(MethodView):
  """Flask view providing a RESTful service discovery resource for all gGRC
  resources, resource collections and services.
  """
  def get(self):
    endpoints = {}
    for entry in services.all_services():
      service = getattr(services, entry.model_class.__name__)
      endpoints[service.__name__] = {
          'href': service.url_for(),
          #TODO additional fields
          #'discoveryVersion': '',
          #'id': '',
          #'name': '',
          #'version': '',
          #'title': '',
          #'description': '',
          #'documentationLink': '',
          }
    endpoints['search'] = { 'href': '/search' }
    endpoints['log_event'] = {'href': '/api/log_events' }
    return self.json_success_response({
        'service_description': {
          'name': 'gGRC-Core',
          'endpoints': endpoints,
          'selfLink': request.url,
          #TODO additional fields
          #'id': '',
          #'title': '',
          #'description': '',
          #'documentationLink': '',
          },
        })

  def json_success_response(
      self, response_object, status=200):
    headers = [
        #('Last-Modified', self.http_timestamp(last_modified)),
        #('Etag', self.etag(response_object)),
        ('Content-Type', 'application/json'),
        #('Location', self.url_for())
        ]
    return current_app.make_response(
      (json.dumps(response_object), status, headers))
