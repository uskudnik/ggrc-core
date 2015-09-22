# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

""" This module is used for import and export of data with csv files """

from ggrc.extensions import get_extension_modules
from ggrc.models import (
    Audit, Control, ControlAssessment, DataAsset, Contract,
    Policy, Regulation, Standard, Facility, Market, Objective,
    OrgGroup, Vendor, Person, Product, Program, Project, Request, Response,
    Section, Clause, System, Process, Issue,
)


def get_shared_unique_rules():
  """ get rules for all cross checks betveen classes

  used for checking unique constraints on colums such as code and title
  """

  shared_tables = [
      (System, Process),
      (Section, Clause),
      (Policy, Regulation, Standard, Contract),
  ]
  rules = {}
  for tables in shared_tables:
    for table in tables:
      rules[table] = tables

  return rules


GGRC_IMPORTABLE = {
    "audit": Audit,
    "control": Control,
    "control assessment": ControlAssessment,
    "control_assessment": ControlAssessment,
    "controlassessment": ControlAssessment,
    "data asset": DataAsset,
    "data_asset": DataAsset,
    "dataasset": DataAsset,
    "contract": Contract,
    "policy": Policy,
    "regulation": Regulation,
    "standard": Standard,
    "facility": Facility,
    "market": Market,
    "objective": Objective,
    "org group": OrgGroup,
    "org_group": OrgGroup,
    "orggroup": OrgGroup,
    "vendor": Vendor,
    "person": Person,
    "product": Product,
    "program": Program,
    "project": Project,
    "request": Request,
    "response": Response,
    "section": Section,
    "clause": Clause,
    "system": System,
    "process": Process,
    "issue": Issue,
}

GGRC_EXPORTABLE = {}


def _get_types(attr):
  res = {}
  for extension_module in get_extension_modules():
    contributed = getattr(extension_module, attr, None)
    if callable(contributed):
      res.update(contributed())
    elif isinstance(contributed, dict):
      res.update(contributed)
  return res


def get_importables():
  """ Get a dict of all importable objects from all modules """
  importable = GGRC_IMPORTABLE
  importable.update(_get_types("contributed_importables"))
  return importable


def get_exportables():
  """ Get a dict of all exportable objects from all modules """
  exportable = GGRC_EXPORTABLE
  exportable.update(get_importables())
  exportable.update(_get_types("contributed_exportables"))
  return exportable
