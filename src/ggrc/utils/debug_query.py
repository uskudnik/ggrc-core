# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Helper functions for debugging queries"""

from sqlalchemy.sql import compiler
from MySQLdb.converters import conversions, escape


def compile_query(session, query):
  """Compile query for MySQL.

  Compile query for current session and return a string representation of
  SQLAlchemy's Query object with filled in parameters.

  The usual `compile_kwargs={"literal_binds": True}` approach suggested by
  SQLALchemy doc (http://docs.sqlalchemy.org/en/latest/faq/sqlexpressions.html#how-do-i-render-sql-expressions-as-strings-possibly-with-bound-parameters-inlined)  # noqa
  doesn't include the backtick characters needed for copy-pasting to console,
  this performs the necessary encoding and escaping.

  Based on http://stackoverflow.com/a/4618647.

  Args:
    session: SQLAlchemy session object
    query: SQLAlchemy Query objects
  Returns:
    Full string representation of SQLAlchemy query
  """
  dialect = session.bind.dialect
  statement = query
  comp = compiler.SQLCompiler(dialect, statement)
  comp.compile()
  enc = dialect.encoding
  params = []
  for key in comp.positiontup:
    value = comp.params[key]
    if isinstance(value, unicode):
      value = value.encode(enc)
    params.append(escape(value, conversions))
  return (comp.string.encode(enc) % tuple(params)).decode(enc)


def explain_query(session, query):
  """Print full EXPLAIN query for SQLAlchemy's Query object

  Args:
    session: SQLAlchemy session object
    query: SQLAlchemy Query objects
  Returns:
    EXPLAIN statement for a given query.
  """
  return "EXPLAIN " + compile_query(session, query)
