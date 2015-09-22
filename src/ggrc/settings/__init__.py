# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Settings for Flask and Flask-SQLAlchemy

Flask: http://flask.pocoo.org/docs/config/
Flask-SQLAlchemy: https://github.com/mitsuhiko/flask-sqlalchemy/blob/master/docs/config.rst

Default settings should go in `settings.default`.

Environment/deployment-specific settings should go in `settings.<environment_name>`.
"""

import os

BASE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..'))
MODULE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
SETTINGS_DIR = os.path.join(BASE_DIR, 'ggrc', 'settings')
THIRD_PARTY_DIR = os.path.realpath(os.path.join(BASE_DIR, '..', 'third_party'))
BOWER_DIR = os.path.realpath(os.path.join(BASE_DIR, '..', 'bower_components'))

from default import *

SETTINGS_MODULE = os.environ.get("GGRC_SETTINGS_MODULE", '')
CUSTOM_URL_ROOT = os.environ.get("GGRC_CUSTOM_URL_ROOT", None)

if len(SETTINGS_MODULE.strip()) == 0:
  raise RuntimeError(
    "Specify your settings using the `GGRC_SETTINGS_MODULE` environment variable")

for module_name in SETTINGS_MODULE.split(" "):
  if len(module_name.strip()) == 0:
    continue

  #logging.info("Loading settings file: {0}".format(module_name))

  filename = "{0}.py".format(module_name)
  fullpath = os.path.join(SETTINGS_DIR, filename)

  if not os.path.exists(fullpath):
    fullpath = "{0}.py".format(os.path.join(*module_name.split('.')))
  if not os.path.exists(fullpath):
    import imp
    module_name_parts = module_name.split('.')
    base_package = module_name_parts[0]
    file, pathname, description = imp.find_module(base_package)
    fullpath = "{0}/{1}.py".format(
        pathname, os.path.join(*module_name_parts[1:]))

  try:
    _EXT = EXTENSIONS if "EXTENSIONS" in vars() else []
    _exports = exports if "exports" in vars() else []
    execfile(fullpath)
    if "EXTENSIONS" in vars() and _EXT != EXTENSIONS:
      _EXT += EXTENSIONS
    EXTENSIONS = _EXT
    del _EXT
    if "exports" in vars() and _exports != exports:
      _exports += exports
    exports = _exports
    del _exports
  except Exception, e:
    raise

#logging.info("SQLALCHEMY_DATABASE_URI: {0}".format(locals().get("SQLALCHEMY_DATABASE_URI", None)))
