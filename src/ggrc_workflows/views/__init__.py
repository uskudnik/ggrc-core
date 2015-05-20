# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from datetime import date, datetime
from flask import render_template, redirect, url_for, current_app
from ggrc.rbac import permissions
from jinja2 import Environment, PackageLoader
from werkzeug.exceptions import Forbidden

from ggrc import db
from ggrc import notification
from ggrc.login import login_required
from ggrc.notification import email
from ggrc_workflows import start_recurring_cycles
from ggrc_workflows.models import Workflow

env = Environment(loader=PackageLoader('ggrc_workflows', 'templates'))

# TODO: move these views to ggrc_views and all the functions to notifications
# module.

def send_error_notification(message):
  try:
    user_email = email.getAppEngineEmail()
    email.send_email(user_email, "Error in nightly cron job", message)
  except Exception as e:
    current_app.logger.error(e)


def run_job(job):
  try:
    job()
  except Exception as e:
    message = "job '{}' failed with: \n{}".format(job.__name__, e.message)
    current_app.logger.error(message)
    send_error_notification(message)


def nightly_cron_endpoint():
  cron_jobs = [
    start_recurring_cycles,
    send_todays_digest_notifications
  ]

  for job in cron_jobs:
    run_job(job)

  return 'Ok'


def modify_data(data):
  """
  for easyer use in templates, it joins the due_in and due today fields
  together
  """

  data["due_soon"] = {}
  if "due_in" in data:
    data["due_soon"].update(data["due_in"])
  if "due_today" in data:
    data["due_soon"].update(data["due_today"])

  # combine "my_tasks" from multiple cycles
  data["cycle_started_tasks"] = {}
  if "cycle_started" in data:
    for cycle in data["cycle_started"].values():
      if "my_tasks" in cycle:
        data["cycle_started_tasks"].update(cycle["my_tasks"])

  return data


def show_pending_notifications():
  if not permissions.is_admin():
    raise Forbidden()
  _, notif_data = notification.get_pending_notifications()

  for day, day_notif in notif_data.iteritems():
    for user_email, data in day_notif.iteritems():
      data = modify_data(data)
  pending = env.get_template("notifications/view_pending_digest.html")
  return pending.render(data=sorted(notif_data.iteritems()))


def show_todays_digest_notifications():
  if not permissions.is_admin():
    raise Forbidden()
  _, notif_data = notification.get_todays_notifications()
  for user_email, data in notif_data.iteritems():
    data = modify_data(data)
  todays = env.get_template("notifications/view_todays_digest.html")
  return todays.render(data=notif_data)


def set_notification_sent_time(notifications):
  for notif in notifications:
    notif.sent_at = datetime.now()
  db.session.commit()


def send_todays_digest_notifications():
  digest_template = env.get_template("notifications/email_digest.html")
  notifications, notif_data = notification.get_todays_notifications()
  sent_emails = []
  subject = "gGRC daily digest for {}".format(date.today().strftime("%b %d"))
  for user_email, data in notif_data.iteritems():
    data = modify_data(data)
    email_body = digest_template.render(digest=data)
    email.send_email(user_email, subject, email_body)
    sent_emails.append(user_email)
  set_notification_sent_time(notifications)
  return "emails sent to: <br> {}".format("<br>".join(sent_emails))


def _get_unstarted_workflows():
  return db.session.query(Workflow).filter(
      Workflow.next_cycle_start_date < date.today(),
      Workflow.recurrences == True,  # noqa
      Workflow.status == 'Active',
  ).all()


def unstarted_cycles():
  workflows = _get_unstarted_workflows()
  return render_template("unstarted_cycles.haml", workflows=workflows)


def start_unstarted_cycles():
  workflows = _get_unstarted_workflows()
  for workflow in workflows:
    workflow.next_cycle_start_date = date.today()
    db.session.add(workflow)
  db.session.commit()
  run_job(start_recurring_cycles)
  return redirect(url_for('unstarted_cycles'))


def init_extra_views(app):
  app.add_url_rule(
      "/nightly_cron_endpoint", "nightly_cron_endpoint",
      view_func=nightly_cron_endpoint)

  app.add_url_rule(
      "/_notifications/show_pending", "show_pending_notifications",
      view_func=login_required(show_pending_notifications))

  app.add_url_rule(
      "/_notifications/show_todays_digest", "show_todays_digest_notifications",
      view_func=login_required(show_todays_digest_notifications))

  app.add_url_rule(
      "/_notifications/send_todays_digest", "send_todays_digest_notifications",
      view_func=send_todays_digest_notifications)

  app.add_url_rule(
      "/admin/unstarted_cycles",
      view_func=login_required(unstarted_cycles))

  app.add_url_rule(
      "/admin/start_unstarted_cycles",
      view_func=login_required(start_unstarted_cycles))
