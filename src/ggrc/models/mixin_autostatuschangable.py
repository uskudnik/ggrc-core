# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: urban@reciprocitylabs.com
# Maintained By: urban@reciprocitylabs.com

from uuid import uuid1

from flask import current_app
from sqlalchemy import and_
from sqlalchemy import event
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import foreign
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates
from sqlalchemy.orm.session import Session

from ggrc import db
from ggrc.models.inflector import ModelInflectorDescriptor
from ggrc.models.reflection import AttributeInfo
from ggrc.models.computed_property import computed_property
from ggrc.models import custom_attribute_value
from ggrc.services.signals import Signals
from ggrc.services.common import Resource

from ggrc.utils import underscore_from_camelcase


class AutoStatusChangable(object):
  __lazy_init__ = True
  _tracked_attrs = set()

  @staticmethod
  def _date_has_changes(attr):
    import datetime
    """Date fields are always interpreted as changed because incoming data is
      of type datetime.datetime, while database field has type datetime.date.
      This function normalises this and performs the correct check.
    """
    if not attr.history.added or not attr.history.deleted:
      return False
    added, deleted = attr.history.added[0], attr.history.deleted[0]
    if isinstance(added, datetime.datetime):
      added = added.date()
    return added != deleted

  @classmethod
  def init(cls, model):
    print "AutoStatusChangable lazy init"
    AutoStatusChangable.set_handlers(model)

  @classmethod
  def set_handlers(cls, model):
    from ggrc.services.common import Resource
    from ggrc.models import relationship
    from ggrc.models.object_document import ObjectDocument

    from sqlalchemy import inspect

    def _get_attr(obj, attribute):
      from ggrc.models import reflection
      if isinstance(attribute, str) or isinstance(attribute, unicode):
        return getattr(inspect(obj).attrs, attribute)
      if isinstance(attribute, reflection.PublishOnly):
        return None

    @Resource.model_put.connect_via(model)
    def handle_object_put(sender, obj=None, src=None, service=None):
      print "\n"*15
      print "handle_object_put"
      has_changes = False

      # for attr in model._tracked_attrs:
      #   print attr, type(attr)
      #   print _get_attr(obj, attr)
      #   if type(attr) != str:
      #     import ipdb;
      #     ipdb.set_trace()
      if any(getattr(inspect(obj).attrs, attr).history.has_changes()
             for attr in model._tracked_attrs):
        has_changes = True

      # print "lets check custom attributes: "
      # print dir(model)
      # print dir(obj)
      #
      # print "\n"*2
      #
      # print dir(inspect(obj).attrs)

      # for attr in inspect(obj).attrs.keys():
      #   print getattr(inspect(obj).attrs, attr).history.has_changes(), getattr(inspect(obj).attrs, attr).history

      # print "\n"*2
      # import ipdb;
      # ipdb.set_trace()

      # for attr in model._tracked_attrs:ac
      #   print "attr: ", attr, getattr(inspect(obj).attrs, attr).history.has_changes(), getattr(inspect(obj).attrs, attr).history.added, getattr(inspect(obj).attrs, attr).history.deleted

      if any(cls._date_has_changes(getattr(inspect(obj).attrs, attr))
             for attr in model._tracked_date_attrs):
        has_changes = True

      if has_changes and obj.status in {"Open", "Final", "Verified"}:
        print "\n" * 5
        print "handle_object_put"
        print "we have changes!"
        obj.status = "In Progress"

    @Signals.custom_attribute_changed.connect_via(model)
    def handle_custom_attribute_save(sender, obj=None, src=None, service=None, *args, **kwargs):
      print "handle_custom_attribute_save: "
      print "obj: ", obj
      print "src: ", src
      print "service: ", service

      if obj.status in {"Open", "Final", "Verified"}:
        obj.status = "In Progress"

    @Resource.model_posted.connect_via(relationship.Relationship)
    @Resource.model_put.connect_via(relationship.Relationship)
    def handle_relationship_post(sender, obj=None, src=None, service=None):
      def adjust_status(obj):
        target_object.status = "In Progress"
        db.session.add(obj)

      has_changes = False
      if model.__name__ in (obj.source.type, obj.destination.type):
        if obj.source.type == model.__name__:
          target_object = obj.source
        else:
          target_object = obj.destination

        if "Document" in {obj.source.type, obj.destination.type} and target_object.status in {"Open", "Final", "Verified"}:
          # This captures the "Add URL" event
          adjust_status(target_object)

        if "Person" in {obj.source.type, obj.destination.type}:
          # This captures assignable addition
          history = inspect(obj).attrs.relationship_attrs.history
          # print "history change: ", history
          # print "attrs:", obj.relationship_attrs["AssigneeType"].attr_value
          if history.has_changes() and target_object.status in {"Final", "Verified"}:
            adjust_status(target_object)

    @Resource.model_posted.connect_via(ObjectDocument)
    def handle_objectdocument_post(sender, obj=None, src=None, service=None):
      # This captures "Attach Evidence" event
      if obj.documentable.type == model.__name__:
        req = obj.documentable
        if req.status in {"Open", "Final", "Verified"}:
          req.status = "In Progress"
          db.session.add(req)

