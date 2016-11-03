# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""This module contains a class for handling request queries."""

# flake8: noqa

import datetime
import collections

import flask
import sqlalchemy as sa

from ggrc import db
from ggrc import models
from ggrc.login import is_creator
from ggrc.fulltext.mysql import MysqlRecordProperty as Record
from ggrc.models import inflector
from ggrc.models.reflection import AttributeInfo
from ggrc.models.relationship_helper import RelationshipHelper
from ggrc.models.custom_attribute_definition import CustomAttributeDefinition
from ggrc.models.custom_attribute_value import CustomAttributeValue
from ggrc.converters import get_exportables
from ggrc.rbac import context_query_filter
from ggrc.utils import query_helpers, benchmark, convert_date_format
from ggrc_basic_permissions import UserRole


class BadQueryException(Exception):
  pass


# pylint: disable=too-few-public-methods

class QueryHelper(object):

  """Helper class for handling request queries

  Primary use for this class is to get list of object ids for each object type
  defined in the query. All objects must pass the query filters if they are
  defined.

  query object = [
    {
      object_name: search class name,
      permissions: either read or update, if none are given it defaults to read
      order_by: [
        {
          "name": the name of the field by which to do the sorting
          "desc": optional; if True, invert the sorting order
        }
      ]
      limit: [from, to] - limit the result list to a slice result[from, to]
      filters: {
        relevant_filters:
          these filters will return all ids of the "search class name" object
          that are mapped to objects defined in the dictionary inside the list.
          [ list of filters joined by OR expression
            [ list of filters joined by AND expression
              {
                "object_name": class of relevant object,
                "slugs": list of relevant object slugs,
                        optional and if exists will be converted into ids
                "ids": list of relevant object ids
              }
            ]
          ],
        object_filters: {
          TODO: allow filtering by title, description and other object fields
        }
      }
    }
  ]

  After the query is done (by `get_ids` method), the results are appended to
  each query object:

  query object with results = [
    {
      object_name: search class name,
      (all other object query fields)
      ids: [ list of filtered objects ids ]
    }
  ]

  The result fields may or may not be present in the resulting query depending
  on the attributes of `get` method.

  """

  def __init__(self, query, ca_disabled=False):
    importable = get_exportables()
    searchable_objects = {o.__name__: o for o in importable.values()}
    # Snapshots aren't importable (yet?) so we have to add it here
    searchable_objects.update({
        "Snapshot": models.Snapshot
    })
    self.object_map = searchable_objects
    self.query = self._clean_query(query)
    self.ca_disabled = ca_disabled
    self._set_attr_name_map()
    self._count = 0

  def _set_attr_name_map(self):
    """ build a map for attributes names and display names

    Dict containing all display_name to attr_name mappings
    for all objects used in the current query
    Example:
        { Program: {"Program URL": "url", "Code": "slug", ...} ...}
    """
    self.attr_name_map = {}
    for object_query in self.query:
      object_name = object_query["object_name"]
      object_class = self.object_map[object_name]
      aliases = AttributeInfo.gather_aliases(object_class)
      self.attr_name_map[object_class] = {}
      for key, value in aliases.items():
        filter_by = None
        if isinstance(value, dict):
          filter_name = value.get("filter_by", None)
          if filter_name is not None:
            filter_by = getattr(object_class, filter_name, None)
          name = value["display_name"]
        else:
          name = value
        if name:
          self.attr_name_map[object_class][name.lower()] = (key.lower(),
                                                            filter_by)

  def _clean_query(self, query):
    """ sanitize the query object """
    for object_query in query:
      filters = object_query.get("filters", {}).get("expression")
      self._clean_filters(filters)
      self._macro_expand_object_query(object_query)
    return query

  def _clean_filters(self, expression):
    """Prepare the filter expression for building the query."""
    if not expression or not isinstance(expression, dict):
      return
    slugs = expression.get("slugs")
    if slugs:
      ids = expression.get("ids", [])
      ids.extend(self._slugs_to_ids(expression["object_name"], slugs))
      expression["ids"] = ids
    try:
      expression["ids"] = [int(id_) for id_ in expression.get("ids", [])]
    except ValueError as error:
      # catch missing relevant filter (undefined id)
      if expression.get("op", {}).get("name", "") == "relevant":
        raise BadQueryException(u"Invalid relevant filter for {}".format(
                                expression.get("object_name", "")))
      raise error
    self._clean_filters(expression.get("left"))
    self._clean_filters(expression.get("right"))

  def _expression_keys(self, exp):
    """Return the list of keys specified in the expression."""
    operator = exp.get("op", {}).get("name", None)
    if operator in ["AND", "OR"]:
      return self._expression_keys(exp["left"]).union(
          self._expression_keys(exp["right"]))
    left = exp.get("left", None)
    if left is not None and isinstance(left, collections.Hashable):
      return set([left])
    else:
      return set()

  def _macro_expand_object_query(self, object_query):
    """Expand object query."""
    def expand_task_dates(exp):
      """Parse task dates from the specified expression."""
      if not isinstance(exp, dict) or "op" not in exp:
        return
      operator = exp["op"]["name"]
      if operator in ["AND", "OR"]:
        expand_task_dates(exp["left"])
        expand_task_dates(exp["right"])
      elif isinstance(exp["left"], (str, unicode)):
        key = exp["left"]
        if key in ["start", "end"]:
          parts = exp["right"].split("/")
          if len(parts) == 3:
            try:
              month, day, year = [int(part) for part in parts]
            except Exception:
              raise BadQueryException(
                  "Date must consist of numbers")
            exp["left"] = key + "_date"
            exp["right"] = datetime.date(year, month, day)
          elif len(parts) == 2:
            month, day = parts
            exp["op"] = {"name": u"AND"}
            exp["left"] = {
                "op": {"name": operator},
                "left": "relative_" + key + "_month",
                "right": month,
            }
            exp["right"] = {
                "op": {"name": operator},
                "left": "relative_" + key + "_day",
                "right": day,
            }
          elif len(parts) == 1:
            exp["left"] = "relative_" + key + "_day"
          else:
            raise BadQueryException(u"Field {} should be a date of one of the"
                                    u" following forms: DD, MM/DD, MM/DD/YYYY"
                                    .format(key))

    if object_query["object_name"] == "TaskGroupTask":
      filters = object_query.get("filters")
      if filters is not None:
        exp = filters["expression"]
        keys = self._expression_keys(exp)
        if "start" in keys or "end" in keys:
          expand_task_dates(exp)

  def get_ids(self):
    """Get a list of filtered object IDs.

    self.query should contain a list of queries for different objects which
    will get evaluated and turned into a list of object IDs.

    Returns:
      list of dicts: same query as the input with all ids that match the filter
    """
    for object_query in self.query:
      objects = self._get_objects(object_query)
      object_query["ids"] = [o.id for o in objects]
    return self.query

  @staticmethod
  def _get_type_query(model, permission_type):
    """Filter by contexts and resources

    Prepare query to filter models based on the available contexts and
    resources for the given type of object.
    """
    contexts, resources = query_helpers.get_context_resource(
        model_name=model.__name__, permission_type=permission_type
    )

    if contexts is not None:
      if resources:
        resource_sql = model.id.in_(resources)
      else:
        resource_sql = sa.sql.false()

      return sa.or_(
        context_query_filter(model.context_id, contexts),
        resource_sql)

  def _get_snapshot_objects(self, object_query, parents, child_type):
    """Creates base query when snapshots are to be returned.

    When snapshots are requested from frontend via relevant_snapshot
    operation we have to build a special query based on
    models.Snapshot objects and not based on model.<Type> but limit
    the results to snapshots that are of type child_type and belong
    to the scopes of selected parents.

    Args:
      object_query: Expression dictionary
      parents: Parent scope objects
      child_type: Type of objects that are to be returned
    Returns:
      Snapshot query object limited to specific parent scopes.
    """
    parent_type = parents["object_name"]
    parent_ids = parents["ids"]
    expression = object_query.get("filters", {}).get("expression")

    if expression is None:
      return set()

    object_class = models.Snapshot
    query = db.session.query(
        models.Snapshot.id,
        models.Snapshot.parent_type,
        models.Snapshot.parent_id,
        models.Snapshot.child_type,
        models.Snapshot.child_id,
        models.Snapshot.revision_id,
        models.Snapshot.updated_at,
    ).filter(
            models.Snapshot.parent_type == parent_type,
            models.Snapshot.parent_id.in_(parent_ids)
    )

    with benchmark("Get permissions: _get_snapshot_objects > _get_type_query"):
      requested_permissions = object_query.get("permissions", "read")
      type_query = self._get_type_query(getattr(models, parent_type),
                                        requested_permissions)
      if type_query is not None:
        query = query.filter(type_query)

    with benchmark(
        "Parse filter query: _get_snapshot_objects > _build_expression"):
      filter_expression = self._build_expression(
          expression,
          object_class,
          parent_type,
          parent_ids,
          child_type
      )
      if filter_expression is not None:
        query = query.filter(filter_expression)

    if object_query.get("order_by"):
      with benchmark("Sorting: _get_snapshot_objects > order_by"):
        pass
    with benchmark("Apply limit"):
      limit = object_query.get("limit")
      if limit:
        matches, total = self._apply_limit(query, limit)
      else:
        matches = query.all()
        total = len(matches)
      object_query["total"] = total
    return matches

  def _get_objects(self, object_query):
    """Get a set of objects described in the filters."""
    object_name = object_query["object_name"]
    expression = object_query.get("filters", {}).get("expression")

    if expression is None:
      return set()
    object_class = self.object_map[object_name]
    query = object_class.query

    requested_permissions = object_query.get("permissions", "read")
    with benchmark("Get permissions: _get_objects > _get_type_query"):
      type_query = self._get_type_query(object_class, requested_permissions)
      if type_query is not None:
        query = query.filter(type_query)
    with benchmark("Parse filter query: _get_objects > _build_expression"):
      filter_expression = self._build_expression(
          expression,
          object_class,
      )
      if filter_expression is not None:
        query = query.filter(filter_expression)
    if object_query.get("order_by"):
      with benchmark("Sorting: _get_objects > order_by"):
        query = self._apply_order_by(
            object_class,
            query,
            object_query["order_by"],
        )
    with benchmark("Apply limit"):
      limit = object_query.get("limit")
      if limit:
        matches, total = self._apply_limit(query, limit)
      else:
        matches = query.all()
        total = len(matches)
      object_query["total"] = total

    if hasattr(flask.g, "similar_objects_query"):
      # delete similar_objects_query for the case when several queries are
      # POSTed in one request, the first one filters by similarity and the
      # second one doesn't but tries to sort by __similarity__
      delattr(flask.g, "similar_objects_query")
    return matches

  @staticmethod
  def _apply_limit(query, limit):
    """Apply limits for pagination.

    Args:
      query: filter query;
      limit: a tuple of indexes in format (from, to); objects is sliced to
            objects[from, to].

    Returns:
      matched objects and total count.
    """
    try:
      first, last = limit
      first, last = int(first), int(last)
    except (ValueError, TypeError):
      raise BadQueryException("Invalid limit operator. Integers expected.")

    if first < 0 or last < 0:
      raise BadQueryException("Limit cannot contain negative numbers.")
    elif first >= last:
      raise BadQueryException("Limit start should be smaller than end.")
    else:
      page_size = last - first
      with benchmark("Apply limit: _apply_limit > query_limit"):
        # Note: limit request syntax is limit:[0,10]. We are counting
        # offset from 0 as the offset of the initial row for sql is 0 (not 1).
        matches = query.limit(page_size).offset(first).all()
      with benchmark("Apply limit: _apply_limit > query_count"):
        if len(matches) < page_size:
          total = len(matches) + first
        else:
          # Note: using func.count() as query.count() is generating additional
          # subquery
          count_q = query.statement.with_only_columns([sa.func.count()])
          total = db.session.execute(count_q).scalar()

    return matches, total

  def _apply_order_by(self, model, query, order_by):
    """Add ordering parameters to a query for objects.

    This works only on direct model properties and related objects defined with
    foreign keys and fails if any CAs are specified in order_by.

    Args:
      model: the model instances of which are requested in query;
      query: a query to get objects from the db;
      order_by: a list of dicts with keys "name" (the name of the field by which
                to sort) and "desc" (optional; do reverse sort if True).

    If order_by["name"] == "__similarity__" (a special non-field value),
    similarity weights returned by get_similar_objects_query are used for
    sorting.

    If sorting by a relationship field is requested, the following sorting is
    applied:
    1. If the field is a relationship to a Titled model, sort by its title.
    2. If the field is a relationship to Person, sort by its name or email (if
       name is None or empty string for a person object).
    3. Otherwise, raise a NotImplementedError.

    Returns:
      the query with sorting parameters.
    """
    def sorting_field_for_person(person):
      """Get right field to sort people by: name if defined or email."""
      return sa.case([(sa.not_(sa.or_(person.name.is_(None),
                                      person.name == '')),
                       person.name)],
                     else_=person.email)

    def joins_and_order(clause):
      """Get join operations and ordering field from item of order_by list.

      Args:
        clause: {"name": the name of model's field,
                 "desc": reverse sort on this field if True}

      Returns:
        ([joins], order) - a tuple of joins required for this ordering to work
                           and ordering clause itself; join is None if no join
                           required or [(aliased entity, relationship field)]
                           if joins required.
      """
      def by_similarity():
        """Join similar_objects subquery, order by weight from it."""
        join_target = flask.g.similar_objects_query.subquery()
        join_condition = model.id == join_target.c.id
        joins = [(join_target, join_condition)]
        order = join_target.c.weight
        return joins, order

      def by_ca():
        """Join fulltext index table, order by indexed CA value."""
        alias = sa.orm.aliased(Record, name=u"fulltext_{}".format(self._count))
        joins = [(alias, sa.and_(
          alias.key == model.id,
          alias.type == model.__name__,
          alias.tags == key)
        )]
        order = alias.content
        return joins, order

      def by_foreign_key():
        """Join the related model, order by title or name/email."""
        related_model = attr.property.mapper.class_
        if issubclass(related_model, models.mixins.Titled):
          joins = [(alias, _)] = [(sa.orm.aliased(attr), attr)]
          order = alias.title
        elif issubclass(related_model, models.Person):
          joins = [(alias, _)] = [(sa.orm.aliased(attr), attr)]
          order = sorting_field_for_person(alias)
        else:
          raise NotImplementedError(u"Sorting by {model.__name__} is "
                                    u"not implemented yet."
                                    .format(model=related_model))
        return joins, order

      def by_m2m():
        """Join the Person model, order by name/email.

        Implemented only for ObjectOwner mapping.
        """
        if issubclass(attr.target_class, models.object_owner.ObjectOwner):
          # NOTE: In the current implementation we sort only by the first
          # assigned owner if multiple owners defined
          oo_alias_1 = sa.orm.aliased(models.object_owner.ObjectOwner)
          oo_alias_2 = sa.orm.aliased(models.object_owner.ObjectOwner)
          oo_subq = db.session.query(
              oo_alias_1.ownable_id,
              oo_alias_1.ownable_type,
              oo_alias_1.person_id,
          ).filter(
              oo_alias_1.ownable_type == model.__name__,
              ~sa.exists().where(sa.and_(
                  oo_alias_2.ownable_id == oo_alias_1.ownable_id,
                  oo_alias_2.ownable_type == oo_alias_1.ownable_type,
                  oo_alias_2.id < oo_alias_1.id,
              )),
          ).subquery()

          owner = sa.orm.aliased(models.Person, name="owner")

          joins = [
              (oo_subq, sa.and_(model.__name__ == oo_subq.c.ownable_type,
                                model.id == oo_subq.c.ownable_id)),
              (owner, oo_subq.c.person_id == owner.id),
          ]

          order = sorting_field_for_person(owner)
        else:
          raise NotImplementedError(u"Sorting by m2m-field '{key}' "
                                    u"is not implemented yet."
                                    .format(key=key))
        return joins, order

      # transform clause["name"] into a model's field name
      key = clause["name"].lower()

      if key == "__similarity__":
        # special case
        if hasattr(flask.g, "similar_objects_query"):
          joins, order = by_similarity()
        else:
          raise BadQueryException("Can't order by '__similarity__' when no ",
                                  "'similar' filter was applied.")
      else:
        key, _ = self.attr_name_map[model].get(key, (key, None))
        attr = getattr(model, key.encode('utf-8'), None)
        if attr is None:
          # non object attributes are treated as custom attributes
          self._count += 1
          joins, order = by_ca()
        elif (isinstance(attr, sa.orm.attributes.InstrumentedAttribute) and
                isinstance(attr.property,
                           sa.orm.properties.RelationshipProperty)):
          joins, order = by_foreign_key()
        elif isinstance(attr, sa.ext.associationproxy.AssociationProxy):
          joins, order = by_m2m()
        else:
          # a simple attribute
          joins, order = None, attr

      if clause.get("desc", False):
        order = order.desc()

      return joins, order

    join_lists, orders = zip(*[joins_and_order(clause) for clause in order_by])
    for join_list in join_lists:
      if join_list is not None:
        for join in join_list:
          query = query.outerjoin(*join)

    return query.order_by(*orders)

  def _build_expression(self, exp, object_class,  # noqa # pylint: disable=too-many-arguments
                        parent_type=None, parent_ids=None, child_type=None):
    # pylint: disable=too-many-locals
    """Make an SQLAlchemy filtering expression from exp expression tree."""
    if "op" not in exp:
      return None

    def autocast(o_key, value):
      """Try to guess the type of `value` and parse it from the string."""
      if not isinstance(o_key, basestring):
        return value

      # isinstance check fails since object_class is of type
      # <class 'flask_sqlalchemy._BoundDeclarativeMeta'>
      if object_class == models.Snapshot:
        return value

      key, _ = self.attr_name_map[object_class].get(o_key, (o_key, None))
      is_date = False
      try:
        attr_type = getattr(object_class, key).property.columns[0].type
      except AttributeError:
        cad = db.session.query(CustomAttributeDefinition).filter(
          CustomAttributeDefinition.title == key,
          CustomAttributeDefinition.definition_type == object_class.__name__,
          CustomAttributeDefinition.
              attribute_type == CustomAttributeDefinition.ValidTypes.DATE,
        ).count()
        if cad:
          is_date = True
      else:
        if isinstance(attr_type, sa.sql.sqltypes.Date):
          is_date = True
      if is_date and isinstance(value, basestring):
        try:
          return convert_date_format(
              value,
              CustomAttributeValue.DATE_FORMAT_JSON,
              CustomAttributeValue.DATE_FORMAT_DB,
          )
        except (TypeError, ValueError):
          raise BadQueryException("Field '{}' expects a '{}' date"
                                  .format(
                                      o_key,
                                      CustomAttributeValue.DATE_FORMAT_JSON,
                                  ))
      return value

    def relevant():
      """Filter by relevant object."""
      query = (self.query[exp["ids"][0]]
               if exp["object_name"] == "__previous__" else exp)
      return object_class.id.in_(
          RelationshipHelper.get_ids_related_to(
              object_class.__name__,
              query["object_name"],
              query["ids"],
          )
      )

    def relevant_snapshot():
      """Filter snapshott scope."""
      return object_class.id.in_(sid for (sid,) in
          db.session.query(models.Snapshot.id).filter(
              models.Snapshot.parent_type == exp["object_name"],
              models.Snapshot.parent_id.in_(exp["ids"]),
              models.Snapshot.child_type == self.query[0]["object_name"]
          ))

    def similar():
      """Filter by relationships similarity."""
      similar_class = self.object_map[exp["object_name"]]
      if not hasattr(similar_class, "get_similar_objects_query"):
        return BadQueryException(u"{} does not define weights to count "
                                 u"relationships similarity"
                                 .format(similar_class.__name__))
      similar_objects_query = similar_class.get_similar_objects_query(
          id_=exp["ids"][0],
          types=[object_class.__name__],
      )
      flask.g.similar_objects_query = similar_objects_query
      similar_objects_ids = [obj.id for obj in similar_objects_query]
      if similar_objects_ids:
        return object_class.id.in_(similar_objects_ids)
      return sa.sql.false()

    def unknown():
      raise BadQueryException(u"Unknown operator \"{}\""
                              .format(exp["op"]["name"]))

    def default_filter_by(object_class, key, predicate):
      """Default filter option that tries to mach predicate in fulltext index.

      This function tries to match the predicate for a give key with entries in
      the full text index table. The key is matched to record tags and as
      the tags only contain custom attribute names, so this filter currently
      only works on custom attributes.

      Args:
        object_class: class of the object we are querying for.
        key: string containing attribute name on which we are filtering.
        predicate: function containing the correct comparison predicate for
          the attribute value.

      Returs:
        Query predicate if the given predicate matches a value for the correct
          custom attribute.
      """
      return object_class.id.in_(db.session.query(Record.key).filter(
              Record.type == object_class.__name__,
              Record.tags == key,
              predicate(Record.content)
          ))

    def snapshots_filter_by(object_class, predicate):
      """Filter snapshot queries to specific parent scope.

      Args:
        object_class: object_class, models.Snapshot in all cases
      Returns:
        IDs from specified parent scope with matching predicate.
      """
      tags = set()
      for _id in parent_ids:
        tags.add("{}-{}-{}".format(parent_type, _id, child_type))

      return object_class.id.in_(db.session.query(Record.key).filter(
        Record.type == "Snapshot",
        Record.tags.in_(tags),
        predicate(Record.content)
      ))

    def with_key(key, p):  # pylint: disable=invalid-name
      """Apply keys to the filter expression."""
      key = key.lower()

      # isinstance check fails since object_class is of type
      # <class 'flask_sqlalchemy._BoundDeclarativeMeta'>
      if object_class == models.Snapshot:
        return snapshots_filter_by(object_class, p)

      key, filter_by = self.attr_name_map[
          object_class].get(key, (key, None))
      if callable(filter_by):
        return filter_by(p)
      else:
        attr = getattr(object_class, key, None)
        if attr:
          return p(attr)
        else:
          return default_filter_by(object_class, key, p)

    with_left = lambda p: with_key(exp["left"], p)

    lift_bin = lambda f: f(self._build_expression(exp["left"], object_class,
                                                  parent_type, parent_ids,
                                                  child_type),
                           self._build_expression(exp["right"], object_class,
                                                  parent_type, parent_ids,
                                                  child_type))

    def text_search():
      """Filter by fulltext search.

      The search is done only in fields indexed for fulltext search.
      """
      return object_class.id.in_(
          db.session.query(Record.key).filter(
              Record.type == object_class.__name__,
              Record.content.ilike(u"%{}%".format(exp["text"])),
          ),
      )

    rhs = lambda: autocast(exp["left"], exp["right"])

    def owned():
      """Get objects for which the user is owner."""
      res = db.session.query(
        query_helpers.get_myobjects_query(
            types=[object_class.__name__],
            contact_id=exp["ids"][0],
            is_creator=is_creator(),
        ).alias().c.id
      )
      res = res.all()
      if res:
        return object_class.id.in_([obj.id for obj in res])
      return sa.sql.false()

    def related_people():
      """Get people related to the specified object."""
      related_type = exp["object_name"]
      related_ids = exp["ids"]
      if "Person" not in [object_class.__name__, related_type]:
        return sa.sql.false()
      model = inflector.get_model(related_type)
      res = []
      res.extend(RelationshipHelper.person_object(
          object_class.__name__,
          related_type,
          related_ids,
      ))

      if related_type in ('Program', 'Audit'):
        res.extend(
            db.session.query(UserRole.person_id).join(model, sa.and_(
                UserRole.context_id == model.context_id,
                model.id.in_(related_ids),
            ))
        )

        if related_type == "Audit":
          res.extend(
              db.session.query(UserRole.person_id).join(
                  models.Program,
                  UserRole.context_id == models.Program.context_id,
              ).join(model, sa.and_(
                  models.Program.id == model.program_id,
                  model.id.in_(related_ids),
              ))
          )
      if "Workflow" in (object_class.__name__, related_type):
        try:
          from ggrc_workflows.models import (relationship_helper as
                                             wf_relationship_handler)
        except ImportError:
          # ggrc_workflows module is not enabled
          return sa.sql.false()
        else:
          res.extend(wf_relationship_handler.workflow_person(
              object_class.__name__,
              related_type,
              related_ids,
          ))
      if res:
        return object_class.id.in_([obj[0] for obj in res])
      return sa.sql.false()

    ops = {
        "AND": lambda: lift_bin(sa.and_),
        "OR": lambda: lift_bin(sa.or_),
        "=": lambda: with_left(lambda l: l == rhs()),
        "!=": lambda: sa.not_(with_left(
                              lambda l: l == rhs())),
        "~": lambda: with_left(lambda l:
                               l.ilike(u"%{}%".format(rhs()))),
        "!~": lambda: sa.not_(with_left(
                              lambda l: l.ilike(u"%{}%".format(rhs())))),
        "<": lambda: with_left(lambda l: l < rhs()),
        ">": lambda: with_left(lambda l: l > rhs()),
        "relevant": relevant,
        "relevant_snapshot": relevant_snapshot,
        "text_search": text_search,
        "similar": similar,
        "owned": owned,
        "related_people": related_people,
    }

    return ops.get(exp["op"]["name"], unknown)()

  def _slugs_to_ids(self, object_name, slugs):
    """Convert SLUG to proper ids for the given objec."""
    object_class = self.object_map.get(object_name)
    if not object_class:
      return []
    ids = [c.id for c in object_class.query.filter(
        object_class.slug.in_(slugs)).all()]
    return ids
