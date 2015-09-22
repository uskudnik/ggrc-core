# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from ggrc.app import app
from ggrc.login import login_required
from flask import render_template


def init_mockup_views():

  @app.route("/mockups/risk-assessment")
  @login_required
  def risk_assessment_redesign():
    """Risk Assessment mockup
    """
    return render_template("/mockups/risk-assessment/index.html")
