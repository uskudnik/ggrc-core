# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: mouli@meics.org
# Maintained By: miha@reciprocitylabs.com


from collections import defaultdict
from datetime import date, datetime
from ggrc.extensions import get_extension_modules
from ggrc.models import Notification, NotificationConfig
from ggrc.utils import merge_dict
from ggrc import db
from sqlalchemy import and_


class NotificationServices():

  def __init__(self):
    self.services = self.all_notifications()

  def all_notifications(self):
    services = {}
    for extension_module in get_extension_modules():
      contributions = getattr(
          extension_module, 'contributed_notifications', None)
      if contributions:
        if callable(contributions):
          contributions = contributions()
        services.update(contributions)
    return services

  def get_service_function(self, name):
    if name not in self.services:
      raise ValueError("unknown service name: %s" % name)
    return self.services[name]

  def call_service(self, name, notification):
    service = self.get_service_function(name)
    return service(notification)


services = NotificationServices()


def get_filter_data(notification):
  result = {}
  data = services.call_service(notification.object_type.name, notification)

  for user, user_data in data.iteritems():
    if should_receive(notification,
                      user_data["force_notifications"][notification.id],
                      user_data["user"]["id"]):
      result[user] = user_data
  return result


def get_notification_data(notifications):
  if not notifications:
    return {}
  aggregate_data = {}

  for notification in notifications:
    filtered_data = get_filter_data(notification)
    aggregate_data = merge_dict(aggregate_data, filtered_data)

  return aggregate_data


def get_pending_notifications():
  notifications = db.session.query(Notification).filter(
      Notification.sent_at == None).all()  # noqa

  notif_by_day = defaultdict(list)
  for notification in notifications:
    notif_by_day[notification.send_on].append(notification)

  data = defaultdict(dict)
  today = datetime.combine(date.today(), datetime.min.time())
  for day, notif in notif_by_day.iteritems():
    current_day = max(day, today)
    data[current_day] = merge_dict(data[current_day],
                                   get_notification_data(notif))

  return notifications, data


def get_todays_notifications():
  notifications = db.session.query(Notification).filter(
      and_(Notification.send_on <= date.today(),
           Notification.sent_at == None  # noqa
           )).all()
  return notifications, get_notification_data(notifications)


def generate_notification_email(data):
  pass


def dispatch_notifications():
  pass


def should_receive(notif, force_notif, person_id, nightly_cron=True):
  def is_enabled(notif_type):
    result = NotificationConfig.query.filter(
        and_(NotificationConfig.person_id == person_id,
             NotificationConfig.notif_type == notif_type))
    # TODO: create_user function should make entries in the notification
    # config table. The code below should not make sure we have default
    # values for new users.
    if result.count() == 0:
      # If we have no results, we need to use the default value, which is
      # true for digest emails.
      return notif_type == "Email_Digest"
    return result.one().enable_flag

  has_instant = force_notif or is_enabled("Email_Now")
  has_digest = force_notif or is_enabled("Email_Digest")

  return has_digest
