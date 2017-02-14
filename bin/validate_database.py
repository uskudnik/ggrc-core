# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Validate audit relationships in a db.

To manually specify a db just export GGRC_DATABASE_URI
Example:
  GGRC_DATABASE_URI="mysql+mysqldb://root:root@localhost/ggrcdev?charset=utf8"
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.

# pylint: disable=invalid-name

import sys
import csv
from collections import defaultdict

# We have to import app before we can use db and other parts of the app.
from ggrc import app  # noqa  pylint: disable=unused-import
from ggrc import db
from ggrc.models import all_models

from ggrc.migrations.utils import validation


def _generate_delete_csv(all_bad_ids):
  """Generate a CSV file for deleting bad objects."""
  data = []
  for model_name, ids in all_bad_ids.items():
    model = getattr(all_models, model_name, None)
    if not model:
      print "Incorrect model found:", model_name
      sys.exit(1)

    slugs = db.session.query(model.slug).filter(model.id.in_(ids))
    data += [
        ["Object type", "", ""],
        [model.__name__, "Code", "Delete"],
    ]
    for row in slugs:
      data.append(["", row.slug, "force"])
    data.append(["", "", ""])

  with open("/vagrant/delete_invalid_data.csv", "wb") as csv_file:
    writer = csv.writer(csv_file)
    for row in data:
      writer.writerow(row)


def validate():
  """Migrate audit-related data and concepts to audit snapshots."""
  return sys.exit(0)
  print "Checking database: {}".format(db.engine)

  tables = set(row[0] for row in db.session.execute("show tables"))

  if {"relationships", "issues", "assessments"}.difference(tables):
    # Ignore checks if required tables do not exist. This is if the check is
    # run on an empty database (usually with db_reset)
    return

  assessment_template_validation = (
      validation.validate_assessment_templates(db.session))

  assessment_relationships_validation = (
      validation.validate_assessment_relationships(db.session))

  request_relationships_validation = (
      validation.validate_request_relationships(db.session))

  issue_relationships_validation = (
      validation.validate_issue_relationships(db.session))

  multiple_mappings, zero_mappings = (
      validation.validate_assessment_issue_to_audit_relationships(db.session))

  all_bad_ids = defaultdict(list)
  validations = [
      multiple_mappings,
      zero_mappings,
      assessment_template_validation,
      request_relationships_validation,
      issue_relationships_validation
  ]
  if any(validations):
    for klass_name, ids in multiple_mappings.items():
      all_bad_ids[klass_name] += ids
      print "Too many Audits mapped to {klass}: {ids}".format(
          klass=klass_name,
          ids=",".join(str(id_) for id_ in sorted(ids))
      )
    for klass_name, ids in zero_mappings.items():
      all_bad_ids[klass_name] += ids
      print "No Audits mapped to {klass}: {ids}".format(
          klass=klass_name,
          ids=",".join(str(id_) for id_ in sorted(ids))
      )
    _generate_delete_csv(all_bad_ids)
    if assessment_template_validation:
      print (
          "The following Assessment Templates are mapped "
          "to multiple Audits: {}".format(
              ",".join(str(id_)
                       for id_, _ in assessment_template_validation)
          ))
    object_validations = [
        ("Assessment", assessment_relationships_validation),
        ("Request", request_relationships_validation),
        ("Issue", issue_relationships_validation),
    ]
    for type_, obj_type_validation in object_validations:
      if obj_type_validation:
        print "The following {} have invalid relationships present: {}".format(
            type_,
            ",".join(str(id_)
                     for id_, in obj_type_validation)
        )

    print ("To remove all violating objects import delete_invalid_data.csv. "
           "Relationships however will not be removed.")
    print "FAIL"
    sys.exit(1)
  else:
    print "PASS"
    sys.exit(0)


if __name__ == "__main__":
  validate()
