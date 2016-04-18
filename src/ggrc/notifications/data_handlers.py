# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

"""Data handlers for notifications for objects in ggrc module.

Main contributed functions are:
  get_assignable_data,
"""

import datetime
import urlparse

from ggrc import utils
from ggrc import models


def get_object_url(obj):
  """Get url for the object info page.

  Args:
    obj (db.Model): Object for which we want to info page url.

  Returns:
    string: Url for the object info page.
  """
  url = "{}/{}".format(obj._inflector.table_plural, obj.id)
  return urlparse.urljoin(utils.get_url_root(), url)


def _get_assignable_dict(people, notif):
  """Get dict data for assignable object in notification.

  Args:
    people (List[Person]): List o people objects who should receive the
      notification.
    notif (Notification): Notification that should be sent.
  Returns:
    dict: dictionary containing notification data for all people in the given
      list.
  """
  obj = get_notification_object(notif)
  data = {}
  for person in people:
    # Requests have "requested_on" field instead of "start_date" and we should
    # default to today() if no appropriate field is found on the object.
    start_date = getattr(obj, "start_date",
                         getattr(obj, "requested_on",
                                 datetime.date.today()))
    data[person.email] = {
        "user": get_person_dict(person),
        notif.notification_type.name: {
            obj.id: {
                "title": obj.title,
                "fuzzy_start_date": utils.get_fuzzy_date(start_date),
                "url": get_object_url(obj),
            }
        }
    }
  return data


def assignable_open_data(notif):
  """Get data for open assignable object.

  Args:
    notif (Notification): Notification entry for an open assignable object.

  Returns:
    A dict containing all notification data for the given notification.
  """
  obj = get_notification_object(notif)
  people = [person for person, _ in obj.assignees]

  return _get_assignable_dict(people, notif)


def _get_declined_people(obj):
  """Get a list of people for declined notifications.

  Args:
    obj (Model): An assignable model

  Returns:
    A list of people that should recieve a declined notification acording to
    the given object type.
  """
  if obj.type == "Request":
    return [person for person, role in obj.assignees
            if "Requester" in role]
  elif obj.type == "Assessment":
    return [person for person, role in obj.assignees
            if "Assessor" in role]
  return []


def assignable_declined_data(notif):
  """Get data for declined assignable object.

  Args:
    notif (Notification): Notification entry for a declined assignable object.

  Returns:
    A dict containing all notification data for the given notification.
  """
  obj = get_notification_object(notif)
  people = _get_declined_people(obj)
  return _get_assignable_dict(people, notif)


def get_person_dict(person):
  """Return dictionary with basic person info.

  Args:
    person (Person): Person object for which we want to get a dictionary.

  Returns:
    dict: dictionary with persons email, name and id.
  """
  if person:
    return {
        "email": person.email,
        "name": person.name,
        "id": person.id,
    }

  return {"email": "", "name": "", "id": -1}


def get_notification_object(notif):
  """Get an object for which the notification entry was made.

  Args:
    notif (Notifications): Notification entry for the given object

  Returns:
    A model based on notif.object_id and notif.object_type.
  """
  model = getattr(models, notif.object_type, None)
  if model:
    return model.query.get(notif.object_id)
  return None


def get_assignable_data(notif):
  """Return data for assignable object notifications.

  Args:
    notif (Notification): notification with an Assignable object_type.

  Returns:
    Dict with all data for the assignable notification or an empty dict if the
    notification is not for a valid assignable object.
  """
  if notif.object_type not in {"Request", "Assessment"}:
    return {}
  elif notif.notification_type.name.endswith("_open"):
    return assignable_open_data(notif)
  elif notif.notification_type.name.endswith("_declined"):
    return assignable_declined_data(notif)
  return {}


def generate_comment_notification(obj, comment, person):
  return {
      "user": get_person_dict(person),
      "comment_created": {
          comment.id: {
              "description": comment.description,
              "parent_type": obj._inflector.title_singular.title(),
              "parent_id": obj.id,
          }
      }
  }


def get_comment_data(notif):
  """Return data for comment notifications.

  This functions checks who should receive the notification and who not, with
  the Commentable mixin that must be added on the object which has the current
  comment. If the object on which the comment was made is not Commentable, the
  function will return an empty dict.

  Args:
    notif (Notification): notification with a Comment object_type.

  Returns:
    Dict with all data needed for sending comment notifications.
  """
  data = {}
  recipients = set()
  comment = get_notification_object(notif)
  rel = (models.Relationship.find_related(comment, models.Request()) or
         models.Relationship.find_related(comment, models.Assessment()))

  if rel:
    comment_obj = (rel.Request_destination or rel.Request_source or
                   rel.Assessment_destination or rel.Assessment_source)

  if comment_obj.recipients:
    recipients = set(comment_obj.recipients.split(","))

  for person, assignee_type in comment_obj.assignees:
    if recipients:
      if recipients.intersection(set(assignee_type)):
        data[person.email] = generate_comment_notification(
            comment_obj, comment, person)
    else:
      data[person.email] = generate_comment_notification(
          comment_obj, comment, person)
  return data
