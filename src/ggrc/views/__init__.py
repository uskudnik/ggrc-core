# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

import json
from collections import namedtuple
from flask import request, session, url_for, redirect, g
from flask.views import View
from ggrc.extensions import get_extension_modules
from ggrc.app import app
from ggrc.rbac import permissions
from ggrc.login import get_current_user
from ggrc.services.common import as_json, inclusion_filter, filter_resource
from ggrc.builder.json import publish, publish_representation
from ggrc.views.converters import *  # necessary for import endpoints
from werkzeug.exceptions import Forbidden
from . import filters
from .registry import object_view
from ggrc.models.background_task import (
    BackgroundTask, queued_task, create_task, make_task_response
    )
from . import notification

"""ggrc.views
Handle non-RESTful views, e.g. routes which return HTML rather than JSON
"""

# Needs to be secured as we are removing @login_required
@app.route("/_background_tasks/reindex", methods=["POST"])
@queued_task
def reindex(task):
  """
  Web hook to update the full text search index
  """

  from ggrc.fulltext import get_indexer
  from ggrc.fulltext.recordbuilder import fts_record_for, model_is_indexed

  indexer = get_indexer()
  indexer.delete_all_records(False)

  from ggrc.models import all_models
  from ggrc.app import db

  # Find all models then remove base classes
  #   (If we don't remove base classes, we get duplicates in the index.)
  inheritance_base_models = [
      all_models.Directive, all_models.SectionBase, all_models.SystemOrProcess,
      all_models.Response
      ]
  models = set(all_models.all_models) - set(inheritance_base_models)
  models = [model for model in models if model_is_indexed(model)]

  for model in models:
    mapper_class = model._sa_class_manager.mapper.base_mapper.class_
    query = model.query.options(
        db.undefer_group(mapper_class.__name__ + '_complete'),
        )
    for query_chunk in generate_query_chunks(query):
      for instance in query_chunk:
        indexer.create_record(fts_record_for(instance), False)
      db.session.commit()

  return app.make_response((
    'success', 200, [('Content-Type', 'text/html')]))

def get_permissions_json():
  permissions.permissions_for(permissions.get_user())
  return json.dumps(getattr(g, '_request_permissions', None))

def get_config_json():
  public_config = dict(app.config.public_config)
  for extension_module in get_extension_modules():
    if hasattr(extension_module, 'get_public_config'):
      public_config.update(
          extension_module.get_public_config(get_current_user()))
  return json.dumps(public_config)

def get_current_user_json():
  from ggrc.models.person import Person
  current_user = get_current_user()
  person = Person.eager_query().filter_by(id=current_user.id).one()
  result = publish_representation(publish(person, (), inclusion_filter))
  return as_json(result)

@app.context_processor
def base_context():
  from ggrc.models import get_model
  return dict(
      get_model=get_model,
      permissions_json=get_permissions_json,
      permissions=permissions,
      config_json=get_config_json,
      current_user_json=get_current_user_json,
      )

from flask import render_template, flash

# Actual HTML-producing routes
#

@app.route("/")
def index():
  """The initial entry point of the app
  """
  from ggrc import settings
  if not settings.PRODUCTION:
    contact = ' For any questions, please contact eng-compliance@google.com.' if settings.GOOGLE_INTERNAL else ""
    flash(u'WARNING - This is not the production instance of the GGRC application.', 'alert alert-warning')
    flash(u'Company confidential, sensitive or personally identifiable information *MUST NOT* be entered or stored here.%s' % (contact), 'alert alert-warning')
  return render_template("welcome/index.haml")

from ggrc.login import login_required

@app.route("/dashboard")
@login_required
def dashboard():
  """The dashboard page
  """
  return render_template("dashboard/index.haml")

def generate_query_chunks(query):
  CHUNK_SIZE = 100
  count = query.count()
  for offset in range(0, count, CHUNK_SIZE):
    yield query.order_by('id').limit(CHUNK_SIZE).offset(offset).all()

@app.route("/admin/reindex", methods=["POST"])
@login_required
def admin_reindex():
  """Calls a webhook that reindexes indexable objects
  """
  from ggrc import settings
  if not permissions.is_allowed_read("/admin", 1):
    raise Forbidden()
  tq = create_task("reindex", url_for(reindex.__name__), reindex)
  return tq.make_response(app.make_response(("scheduled %s" % tq.name,
                                            200,
                                            [('Content-Type', 'text/html')])))

@app.route("/admin")
@login_required
def admin():
  """The admin dashboard page
  """
  if not permissions.is_allowed_read("/admin", 1):
    raise Forbidden()
  return render_template("admin/index.haml")


@app.route("/background_task/<id_task>", methods=['GET'])
def get_task_response(id_task):
  return make_task_response(id_task)


def contributed_object_views():
  from ggrc import models
  from .common import RedirectedPolymorphView

  return [
      object_view(models.BackgroundTask),
      object_view(models.Program),
      object_view(models.Audit),
      object_view(models.Directive, RedirectedPolymorphView),
      object_view(models.Contract),
      object_view(models.Policy),
      object_view(models.Regulation),
      object_view(models.Standard),
      object_view(models.Clause),
      object_view(models.Section),
      object_view(models.Control),
      object_view(models.ControlAssessment),
      object_view(models.Objective),
      object_view(models.System),
      object_view(models.Process),
      object_view(models.Product),
      object_view(models.Request),
      object_view(models.OrgGroup),
      object_view(models.Facility),
      object_view(models.Market),
      object_view(models.Project),
      object_view(models.DataAsset),
      object_view(models.Person),
      object_view(models.Vendor),
      object_view(models.Issue),
  ]


def all_object_views():
  views = contributed_object_views()

  for extension_module in get_extension_modules():
    contributions = getattr(extension_module, "contributed_object_views", None)
    if contributions:
      if callable(contributions):
        contributions = contributions()
      views.extend(contributions)

  return views


def init_extra_views(app):
  pass


def init_all_views(app):
  import sys
  from ggrc import settings

  for entry in all_object_views():
    entry.service_class.add_to(
      app,
      '/{0}'.format(entry.url),
      entry.model_class,
      decorators=(login_required,)
      )

  init_extra_views(app)
  for extension_module in get_extension_modules():
    ext_extra_views = getattr(extension_module, "init_extra_views", None)
    if ext_extra_views:
      ext_extra_views(app)


# Mockups HTML pages are listed here
@app.route("/mockups/v1.0/program.html")
@login_required
def mockup():
  """The mockup program guide page
  """
  return render_template("mockups/v1.0/program.html")

@app.route("/mockups/v1.0/assessment.html")
@login_required
def assessments():
  """The assessments guide page
  """
  return render_template("mockups/v1.0/assessment.html")

@app.route("/mockups/v1.0/assessment-start.html")
@login_required
def assessments_start():
  """The assessment start guide page
  """
  return render_template("mockups/v1.0/assessment-start.html")

@app.route("/mockups/v1.0/object.html")
@login_required
def assessments_object():
  """The assessment object guide page
  """
  return render_template("mockups/v1.0/object.html")

@app.route("/mockups/v1.0/object-final.html")
@login_required
def assessments_object_final():
  """The assessment object final guide page
  """
  return render_template("mockups/v1.0/object-final.html")

@app.route("/mockups/v1.0/my-work.html")
@login_required
def assessments_my_work():
  """The assessment my work guide page
  """
  return render_template("mockups/v1.0/my-work.html")

@app.route("/mockups/assessments_grid")
@login_required
def assessments_grid():
  """The assessments grid guide page
  """
  return render_template("mockups/assessments-grid.html")

@app.route("/mockups/v1.1/index.html")
@login_required
def workflow_assessment():
  """The workflow assessment guide page
  """
  return render_template("mockups/v1.1/index.html")

@app.route("/mockups/v1.1/workflow.html")
@login_required
def workflow_info():
  """The workflow info guide page
  """
  return render_template("mockups/v1.1/workflow.html")

@app.route("/mockups/rapid-data-entry/index.html")
@login_required
def rapid_data_entry():
  """Rapid data entry mockup
  """
  return render_template("mockups/rapid-data-entry/index.html")

@app.route("/mockups/custom-attributes/index.html")
@login_required
def custom_attributes():
  """Custom attributes mockup
  """
  return render_template("mockups/custom-attributes/index.html")

@app.route("/mockups/reporting/index.html")
@login_required
def reporting():
  """Reporting mockup
  """
  return render_template("mockups/reporting/index.html")

@app.route("/mockups/dashboard-ui/index.html")
@login_required
def dashboard_ui():
  """Dashboard UI UX mockup
  """
  return render_template("mockups/dashboard-ui/index.html")

@app.route("/mockups/dashboard-ui/object.html")
@login_required
def object_ui():
  """Object UI UX mockup
  """
  return render_template("mockups/dashboard-ui/object.html")

@app.route("/mockups/dashboard-ui/tree.html")
@login_required
def tree_ui():
  """Tree UI UX mockup
  """
  return render_template("/mockups/dashboard-ui/tree.html")

@app.route("/mockups/dashboard-ui/workflow.html")
@login_required
def workflow_ui():
  """Workflow UI UX mockup
  """
  return render_template("/mockups/dashboard-ui/workflow.html")

@app.route("/mockups/dashboard-ui/workflow-info.html")
@login_required
def workflow_info_ui():
  """Workflow info UI UX mockup
  """
  return render_template("/mockups/dashboard-ui/workflow-info.html")

@app.route("/mockups/dashboard-ui/workflow-people.html")
@login_required
def workflow_people_ui():
  """Workflow people UI UX mockup
  """
  return render_template("/mockups/dashboard-ui/workflow-people.html")

@app.route("/mockups/dashboard-ui/audit.html")
@login_required
def audit_ui():
  """Audit UI UX mockup
  """
  return render_template("/mockups/dashboard-ui/audit.html")

@app.route("/mockups/dashboard-ui/audit-info.html")
@login_required
def audit_info_ui():
  """Audit info UI UX mockup
  """
  return render_template("/mockups/dashboard-ui/audit-info.html")

@app.route("/mockups/dashboard-ui/audit-people.html")
@login_required
def audit_people_ui():
  """Audit people UI UX mockup
  """
  return render_template("/mockups/dashboard-ui/audit-people.html")

@app.route("/mockups/audit-revamp/info.html")
@login_required
def audit_info_revamp():
  """Audit info revamp mockup
  """
  return render_template("/mockups/audit-revamp/info.html")

@app.route("/mockups/audit-revamp/issues.html")
@login_required
def audit_info_issues_revamp():
  """Audit info issues revamp mockup
  """
  return render_template("/mockups/audit-revamp/issues.html")

@app.route("/mockups/audit-3.0/")
@login_required
def audit_3_0():
  """Audit 3.0 mockup
  """
  return render_template("/mockups/audit-3.0/info.html")

@app.route("/mockups/audit-3.0/control-assessment.html")
@login_required
def audit_3_0_ca():
  """Audit 3.0 CA mockup
  """
  return render_template("/mockups/audit-3.0/control-assessment.html")

@app.route("/permissions")
@login_required
def user_permissions():
  '''Permissions object for the currently
     logged in user
  '''
  return get_permissions_json()
