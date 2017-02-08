# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Services for Search API"""

import json

from flask import request, current_app

import ggrc.models.relationship

from ggrc.fulltext import get_indexer
from ggrc.utils import GrcEncoder, url_for, benchmark
from ggrc import db


def search():
  with benchmark("search.py:search"):
    terms = request.args.get('q')
    permission_type = request.args.get('__permission_type', 'read')
    permission_model = request.args.get('__permission_model', None)
    if terms is None:
      return current_app.make_response((
          'Query parameter "q" specifying search terms must be provided.',
          400,
          [('Content-Type', 'text/plain')],
      ))

    should_group_by_type = request.args.get('group_by_type', '')
    should_group_by_type = should_group_by_type.lower() == 'true'
    should_just_count = request.args.get('counts_only', '')
    should_just_count = should_just_count.lower() == 'true'

    types = request.args.get('types', '')
    types = [t.strip() for t in types.split(',') if len(t.strip()) > 0]
    if len(types) == 0:
      types = None

    contact_id = request.args.get('contact_id')
    extra_params = request.args.get('extra_params', {})
    extra_columns = request.args.get('extra_columns', {})

    relevant_objects = request.args.get('relevant_objects', None)

    if extra_params:
      # Parse t1:a=b,c=d;t2:e=f into dict {t1:{a:b,c:d},t2:{e:f}}
      extra_params = {
          k: {
              kk: vv for kk, vv in (x.split('=') for x in v.split(','))
          } for k, v in (x.split(':') for x in extra_params.split(';'))
      }
    else:
      extra_params = {}

    if extra_columns:
      # Parse a=b,c=d into dict {a:b,c:d}
      extra_columns = {k: v for k, v in
                       (x.split('=') for x in extra_columns.split(','))}

    else:
      extra_columns = {}

    if relevant_objects is not None:
      relevant_objects = [tuple(obj.split(':'))
                          for obj in relevant_objects.split(',')]

    if should_just_count:
      return do_counts(terms, types, contact_id, extra_params, extra_columns)
    if should_group_by_type:
      return group_by_type_search(terms, types, contact_id, extra_params,
                                  relevant_objects)
    return basic_search(
        terms, types,
        permission_type, permission_model,
        contact_id, extra_params, relevant_objects
    )


def do_counts(terms, types=None, contact_id=None,
              extra_params={}, extra_columns={}):
  # FIXME: ? This would make the query more efficient, but will also prune
  #   objects the user is allowed to read in other contexts.
  # Remove types that the user can't read
  # types = [type for type in types if permissions.is_allowed_read(type, None)]

  with benchmark("search.py:do_counts"):
    indexer = get_indexer()
    with benchmark("Counts"):
      results = indexer.counts(terms, types=types, contact_id=contact_id,
                               extra_params=extra_params,
                               extra_columns=extra_columns)

    results = [(r[2] if r[2] != "" else r[0], r[1]) for r in results]
    return current_app.make_response((
        json.dumps({
            'results': {
                'selfLink': request.url,
                'counts': dict(results)
            }
        }, cls=GrcEncoder),
        200,
        [('Content-Type', 'application/json')],
    ))


def _build_relevant_filter(types, relevant_objects):
  with benchmark("search.py:_build_relevant_filter"):
    if relevant_objects is None:
      relevant_objects = []
    filters = []
    for relevant_type, relevant_id in relevant_objects:
      relationship = ggrc.models.relationship.Relationship
      src_query = db.session.query(
          relationship.source_type, relationship.source_id
      ).filter(
          relationship.source_type.in_(types) | (types is None),
          relationship.destination_type == relevant_type,
          relationship.destination_id == relevant_id
      )
      dst_query = db.session.query(
          relationship.destination_type, relationship.destination_id
      ).filter(
          relationship.destination_type.in_(types) | (types is None),
          relationship.source_type == relevant_type,
          relationship.source_id == relevant_id
      )
      filters.append(set(src_query.union(dst_query)))

    def check(result_pair):
      return all(result_pair in bucket for bucket in filters)

    return check


def do_search(terms, list_for_type, types=None, permission_type='read',
              permission_model=None, contact_id=None, extra_params=None,
              relevant_objects=None):
  with benchmark("search.py:do_search"):
    indexer = get_indexer()
    results = indexer.search(
        terms, types=types, permission_type=permission_type,
        permission_model=permission_model, contact_id=contact_id,
        extra_params=extra_params
    )

    related_filter = _build_relevant_filter(types, relevant_objects)
    seen_results = {}

    with benchmark("build_results"):
      for result in results:
        id = result.key
        model_type = result.type
        result_pair = (model_type, id)
        if result_pair not in seen_results and related_filter(result_pair):
          seen_results[result_pair] = True
          entries_list = list_for_type(model_type)
          entries_list.append({
              'id': id,
              'type': model_type,
              'href': url_for(model_type, id=id),
          })


def make_search_result(entries):
  with benchmark("search.py:make_search_result"):
    return current_app.make_response((
        json.dumps({
            'results': {
                'selfLink': request.url,
                'entries': entries,
            }
        }, cls=GrcEncoder),
        200,
        [('Content-Type', 'application/json')],
    ))


def basic_search(terms, types=None,
                 permission_type='read', permission_model=None,
                 contact_id=None, extra_params=None, relevant_objects=None):
  with benchmark("search.py:basic_search"):
    entries = []

    def list_for_type(_):
      return entries

    do_search(terms, list_for_type, types, permission_type, permission_model,
              contact_id, extra_params, relevant_objects)
    return make_search_result(entries)


def group_by_type_search(terms, types=None, contact_id=None, extra_params={},
                         relevant_objects=None):
  with benchmark("search.py:group_by_type_search"):
    entries = {}

    def list_for_type(t):
      return entries[t] if t in entries else entries.setdefault(t, [])

    do_search(terms, list_for_type, types, contact_id=contact_id,
              extra_params=extra_params, relevant_objects=relevant_objects)
    return make_search_result(entries)
