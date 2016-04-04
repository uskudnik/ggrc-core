# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from ggrc.models.all_models import *
from ggrc import settings
from ggrc import db

"""All gGRC model objects and associated utilities."""

def create_db_with_create_all():
  import ggrc.models.all_models

  db.create_all()

def create_db_with_migrations(quiet=False):
  from ggrc.migrate import upgradeall
  import logging

  if quiet:
    logging.disable(logging.INFO)
  upgradeall()

  if quiet:
    logging.disable(logging.NOTSET)

def drop_db_with_drop_all():
  import ggrc.models.all_models

  if 'mysql' in settings.SQLALCHEMY_DATABASE_URI:
    db.engine.execute('SET FOREIGN_KEY_CHECKS = 0')

  db.drop_all()

def drop_db_with_migrations(quiet=False):
  from ggrc.migrate import downgradeall
  import ggrc.models.all_models
  import logging

  if quiet:
    logging.disable(logging.INFO)
  if 'mysql' in settings.SQLALCHEMY_DATABASE_URI:
    db.engine.execute('SET FOREIGN_KEY_CHECKS = 0')
  downgradeall(drop_versions_table=True)
  if quiet:
    logging.disable(logging.NOTSET)
  if 'mysql' in settings.SQLALCHEMY_DATABASE_URI:
    db.engine.execute('SET FOREIGN_KEY_CHECKS = 1')

def create_db(use_migrations=False, quiet=False):
  if 'mysql' in settings.SQLALCHEMY_DATABASE_URI:
    db.engine.execute('SET FOREIGN_KEY_CHECKS = 0')

  if use_migrations:
    create_db_with_migrations(quiet)
  else:
    create_db_with_create_all()

  if 'mysql' in settings.SQLALCHEMY_DATABASE_URI:
    db.engine.execute('SET FOREIGN_KEY_CHECKS = 1')


def drop_db(use_migrations=False, quiet=False):
  if use_migrations:
    drop_db_with_migrations(quiet)
  else:
    drop_db_with_drop_all()


def init_models(app):
  from .all_models import all_models
  [model._inflector for model in all_models]


def init_all_models(app):
  """Register all gGRC models services with the Flask application ``app``."""

  from ggrc.extensions import get_extension_modules

  # Usually importing the module is enough, but just in case, also invoke
  # ``init_models``
  init_models(app)
  for extension_module in get_extension_modules():
    ext_init_models = getattr(extension_module, 'init_models', None)
    if ext_init_models:
      ext_init_models(app)

def init_lazy_mixins(app):
  from ggrc.models import all_models
  import inspect
  for model in all_models.all_models:
    for mixin in inspect.getmro(model):
      if hasattr(mixin, '__lazy_init__') and getattr(mixin, '__lazy_init__'):
        mixin.init(model)

def init_session_monitor_cache():
  from sqlalchemy.orm.session import Session
  from sqlalchemy import event
  from .cache import Cache
  from ggrc.services.common import get_cache

  def update_cache_before_flush(session, flush_context, objects):
    cache = get_cache(create = True)
    if cache:
      cache.update_before_flush(session, flush_context)

  def update_cache_after_flush(session, flush_context):
    cache = get_cache(create = False)
    if cache:
      cache.update_after_flush(session, flush_context)

  def clear_cache(session):
    cache = get_cache()
    if cache:
      cache.clear()

  event.listen(Session, 'before_flush', update_cache_before_flush)
  event.listen(Session, 'after_flush', update_cache_after_flush)
  event.listen(Session, 'after_commit', clear_cache)
  event.listen(Session, 'after_rollback', clear_cache)


def init_sanitization_hooks():
  # Register event listener on all String and Text attributes to sanitize them.
  import bleach
  from HTMLParser import HTMLParser
  import sqlalchemy as sa
  from ggrc.models.reflection import SanitizeHtmlInfo
  from .all_models import all_models

  # Set up custom tags/attributes for bleach
  bleach_tags = [
      'caption', 'strong', 'em', 'b', 'i', 'p', 'code', 'pre', 'tt', 'samp',
      'kbd', 'var', 'sub', 'sup', 'dfn', 'cite', 'big', 'small', 'address',
      'hr', 'br', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul',
      'ol', 'li', 'dl', 'dt', 'dd', 'abbr', 'acronym', 'a', 'img',
      'blockquote', 'del', 'ins', 'table', 'tbody', 'tr', 'td', 'th',
      ] + bleach.ALLOWED_TAGS
  bleach_attrs = {}
  attrs = [
      'href', 'src', 'width', 'height', 'alt', 'cite', 'datetime',
      'title', 'class', 'name', 'xml:lang', 'abbr'
      ]

  for tag in bleach_tags:
    bleach_attrs[tag] = attrs

  def cleaner(target, value, oldvalue, initiator):
    # Some cases like Request don't use the title value
    #  and it's nullable, so check for that
    if value is None:
      return value

    parser = HTMLParser()
    value = unicode(value)
    lastvalue = value
    value = parser.unescape(value)
    while value != lastvalue:
      lastvalue = value
      value = parser.unescape(value)

    ret = parser.unescape(
      bleach.clean(value, bleach_tags, bleach_attrs, strip=True)
      )
    return ret

  for model in all_models:
    attr_info = SanitizeHtmlInfo(model)
    for attr_name in attr_info._sanitize_html:
      attr = getattr(model, attr_name)
      sa.event.listen(attr, 'set', cleaner, retval=True)


def init_app(app):
  init_all_models(app)
  init_lazy_mixins(app)
  init_session_monitor_cache()
  init_sanitization_hooks()

from .inflector import get_model
