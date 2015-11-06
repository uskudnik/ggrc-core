# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

import os
import logging
from flask.ext.testing import TestCase as BaseTestCase
from ggrc import db
from ggrc.app import app
from ggrc.models import create_db

if os.environ.get('TRAVIS', False):
  db.engine.execute("DROP DATABASE IF EXISTS ggrcdevtest;")
  db.engine.execute("CREATE DATABASE ggrcdevtest; USE ggrcdevtest;")

  create_db(use_migrations=True, quiet=True)

# Hide errors during testing. Errors are still displayed after all tests are
# done. This is for the bad request error messages while testing the api calls.
logging.disable(logging.CRITICAL)


class TestCase(BaseTestCase):

  maxDiff = None

  @classmethod
  def clear_data(cls):
    ignore_tables = (
        "test_model", "roles", "notification_types", "object_types", "options",
        "categories",
    )
    tables = set(db.metadata.tables).difference(ignore_tables)
    for _ in range(len(tables)):
      if len(tables) == 0:
        break  # stop the loop once all tables have been deleted
      for table in reversed(db.metadata.sorted_tables):
        if table.name not in ignore_tables:
          try:
            db.engine.execute(table.delete())
            tables.remove(table.name)
          except:
            pass

    db.session.commit()


  def setUp(self):
    # this is a horrible hack because db.metadata.sorted_tables does not sort
    # by dependencies. Events table is before Person table - reversed is bad.
    self.clear_data()

    # if getattr(settings, 'MEMCACHE_MECHANISM', False) is True:
    #   from google.appengine.api import memcache
    #   from google.appengine.ext import testbed
    #   self.testbed = testbed.Testbed()
    #   self.testbed.activate()
    #   self.testbed.init_memcache_stub()

  def tearDown(self):
    db.session.remove()

    # if getattr(settings, 'MEMCACHE_MECHANISM', False) is True:
    #   from google.appengine.api import memcache
    #   from google.appengine.ext import testbed
    #   self.testbed.deactivate()

  def create_app(self):
    app.config["SERVER_NAME"] = "localhost"
    app.testing = True
    app.debug = False
    return app
