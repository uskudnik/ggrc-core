# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from flask import json
from os.path import abspath
from os.path import dirname
from os.path import join

from integration import ggrc


THIS_ABS_PATH = abspath(dirname(__file__))


class TestCase(ggrc.TestCase):

  CSV_DIR = join(THIS_ABS_PATH, "test_csvs/")

  def import_file(self, filename, dry_run=False):
    data = {"file": (open(join(self.CSV_DIR, filename)), filename)}
    headers = {
        "X-test-only": "true" if dry_run else "false",
        "X-requested-by": "gGRC",
    }
    response = self.client.post("/_service/import_csv",
                                data=data, headers=headers)
    self.assert200(response)
    return json.loads(response.data)

  def export_csv(self, data):
    headers = {
        'Content-Type': 'application/json',
        "X-requested-by": "gGRC",
        "X-export-view": "blocks",
    }
    return self.client.post("/_service/export_csv", data=json.dumps(data),
                            headers=headers)
