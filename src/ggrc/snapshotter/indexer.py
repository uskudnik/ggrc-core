# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Manage indexing for snapshotter service"""

from sqlalchemy.sql.expression import tuple_

from ggrc import db
from ggrc import models
from ggrc.fulltext.mysql import MysqlRecordProperty as Record
from ggrc.models.reflection import AttributeInfo

from ggrc.snapshotter.rules import Types
from ggrc.snapshotter.datastructures import Pair


def _get_tag(pair):
  return u"{parent_type}-{parent_id}-{child_type}".format(**{
      "parent_type": pair.parent.type,
      "parent_id": pair.parent.id,
      "child_type": pair.child.type,
  })


def _get_parent_property(pair):
  return u"{parent_type}-{parent_id}".format(**{
      "parent_type": pair.parent.type,
      "parent_id": pair.parent.id,
  })


def _get_child_property(pair):
  return u"{child_type}-{child_id}".format(**{
      "child_type": pair.child.type,
      "child_id": pair.child.id,
  })


def _get_columns():
  """Get common columns for snapshots and revisions tables."""

  snapshot_columns = db.session.query(
      models.Snapshot.id,
      models.Snapshot.context_id,
      models.Snapshot.parent_type,
      models.Snapshot.parent_id,
      models.Snapshot.child_type,
      models.Snapshot.child_id,
      models.Snapshot.revision_id
  )
  revision_columns = db.session.query(
      models.Revision.id,
      models.Revision.resource_type,
      models.Revision.content
  )
  return snapshot_columns, revision_columns


def _get_revision_content(revision_ids=None):
  """Get content for provided revision_ids

  Args:
    revision_ids: An iterable of revision IDs
  Returns:
    Dictionary mapping revision_ids to content.
  """
  revision_dict = dict()
  if revision_ids:
    revisions = db.session.query(
        models.Revision.id,
        models.Revision.content).filter(models.Revision.id.in_(revision_ids))
    for rid, rcontent in revisions:
      revision_dict[rid] = rcontent
  return revision_dict


def _get_model_properties():
  """Get indexable properties for all snapshottable objects

  Args:
    None
  Returns:
    tuple(class_properties dict, custom_attribute_definitions dict) - Tuple of
        dictionaries, first one representing a list of searchable attributes
        for every model and second one representing dictionary of custom
        attribute definition attributes.
  """
  # pylint: disable=protected-access
  from ggrc.models import all_models
  class_properties = dict()
  custom_attribute_definitions = dict()
  klass_names = Types.all

  cadef_klass_names = {
      getattr(all_models, klass)._inflector.table_singular
      for klass in klass_names
  }

  cad_query = db.session.query(
      models.CustomAttributeDefinition.id,
      models.CustomAttributeDefinition.title,
  ).filter(
      models.CustomAttributeDefinition.definition_type.in_(cadef_klass_names),
      models.CustomAttributeDefinition.attribute_type.in_(
          ["Text", "Rich Text", "Date"])
  )

  for cad in cad_query:
    custom_attribute_definitions[cad[0]] = cad[1]

  for klass_name in klass_names:
    model_attributes = AttributeInfo.gather_attrs(
        getattr(all_models, klass_name), '_fulltext_attrs')
    class_properties[klass_name] = model_attributes

  return class_properties, custom_attribute_definitions


def get_searchable_attributes(attributes, cad_keys,
                              ca_definitions, content):
  """Get all searchable attributes for a given object that should be indexed

  Args:
    attributes: Attributes that should be extracted from some model
    cad_keys: IDs of custom attribute definitions
    ca_definitions: Dictionary of "CAD ID" -> "CAD title"
    content: dictionary (JSON) representation of an object
  Return:
    Dict of "key": "value" from objects revision
  """
  searchable_values = dict()
  for attr in attributes:
    if attr in content:
      searchable_values[attr] = content[attr]

  if "custom_attributes" in content and content["custom_attributes"]:
    for cav in content["custom_attributes"]:
      cav_id = cav["custom_attribute_id"]
      if cav_id in cad_keys:
        searchable_values[ca_definitions[cav_id]] = cav["attribute_value"]
  return searchable_values


def reindex(parents=None):
  """Reindex all snapshots or limit to a subset of certain parents.

  Args:
    parents: An iterable of parents for which to reindex their scopes.
  Returns:
    Pair of parent-child that were reindexed.
  """
  columns = db.session.query(
      models.Snapshot.parent_type,
      models.Snapshot.parent_id,
      models.Snapshot.child_type,
      models.Snapshot.child_id,
  )
  query = columns
  if parents:
    _parents = {(obj.type, obj.id) for obj in parents}
    query = query.filter(
        tuple_(
            models.Snapshot.parent_type,
            models.Snapshot.parent_id,
        ).in_(_parents))

  pairs = {Pair.from_4tuple(p) for p in query}
  reindex_pairs(pairs)
  return pairs


def delete_records(snapshot_ids):
  """Delete all records for some snapshots.
  Args:
    snapshot_ids: An iterable with snapshot IDs whose full text records should
        be deleted.
  """
  to_delete = {("Snapshot", _id) for _id in snapshot_ids}
  db.session.query(Record).filter(
      tuple_(Record.type, Record.key).in_(to_delete)
  ).delete(synchronize_session=False)
  db.session.commit()


def insert_records(payload):
  """Insert records to full text table.

  Args:
    payload: List of dictionaries that represent records entries.
  """
  engine = db.engine
  engine.execute(Record.__table__.insert(), payload)
  db.session.commit()


def reindex_pairs(pairs):
  """Reindex selected snapshots.

  Args:
    pairs: A list of parent-child pairs that uniquely represent snapshot
    object whose properties should be reindexed.
  """

  # pylint: disable=too-many-locals
  snapshots = dict()
  revisions = dict()
  snap_to_sid_cache = dict()
  search_payload = list()

  object_properties, custom_attr_def_properties = _get_model_properties()
  ca_def_keys = set(custom_attr_def_properties.keys())

  snapshot_columns, revision_columns = _get_columns()

  snapshot_query = snapshot_columns
  if pairs:
    pairs_filter = tuple_(
        models.Snapshot.parent_type,
        models.Snapshot.parent_id,
        models.Snapshot.child_type,
        models.Snapshot.child_id,
    ).in_({pair.to_4tuple() for pair in pairs})
    snapshot_query = snapshot_columns.filter(pairs_filter)

    for _id, ctx_id, ptype, pid, ctype, cid, revid in snapshot_query:
      pair = Pair.from_4tuple((ptype, pid, ctype, cid))
      snapshots[pair] = [_id, ctx_id, revid]
      snap_to_sid_cache[pair] = _id

    revision_ids = {revid for _, _, revid in snapshots.values()}
    revision_query = revision_columns.filter(
        models.Revision.id.in_(revision_ids)
    )
    for _id, _type, content in revision_query:
      revisions[_id] = get_searchable_attributes(
          object_properties[_type], ca_def_keys, custom_attr_def_properties,
          content)

    snapshot_ids = set()
    for pair in snapshots:
      snapshot_id, ctx_id, revision_id = snapshots[pair]
      snapshot_ids.add(snapshot_id)

      properties = revisions[revision_id]
      properties.update({
          "parent": _get_parent_property(pair),
          "child": _get_child_property(pair),
          "child_type": pair.child.type,
          "child_id": pair.child.id
      })

      for prop, val in properties.items():
        if prop and val:
          data = {
              "key": snapshot_id,
              "type": "Snapshot",
              "context_id": ctx_id,
              "tags": _get_tag(pair),
              "property": prop,
              "content": val,
          }
          search_payload += [data]

    delete_records(snapshot_ids)
    insert_records(search_payload)
