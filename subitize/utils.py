"""Utilities for subitize."""

import sqlparse
from sqlalchemy.dialects import sqlite

def print_sql(query):
    """Pretty print a SQL query.

    Arguments:
        query (Query): A sqlalchemy query object.
    """
    sql = str(query.statement.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True}))
    print(sqlparse.format(sql, reindent=True, keyword_case='upper'))
