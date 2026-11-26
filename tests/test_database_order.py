"""Regression tests for the sort-order allow-list in spotisub.database.

Every list page takes its sort column from the URL
(``/overview/<page>/<limit>/<order>/`` and friends) and
``database.limit_and_order_stmt()`` interpolated that string into a raw SQL
``ORDER BY`` fragment. Whatever the caller put in the path was therefore
executed by SQLite, so a URL such as
``/overview/1/25/case%20when%20(select%20...)`` was a working blind SQL
injection for anyone who could open the page.
``resolve_order_column()`` now only passes through ``table.column`` pairs
that exist in the schema.
"""
from sqlalchemy import select

from spotisub import database


def _compiled(stmt):
    return str(stmt.compile(compile_kwargs={"literal_binds": True}))


def test_known_column_is_kept_for_sorting():
    """A real ``table.column`` pair still sorts the page."""
    assert database.resolve_order_column(
        "spotify_song.title") == "spotify_song.title"
    stmt = database.limit_and_order_stmt(
        select(database.dbms.spotify_song.c.title),
        order="spotify_song.title", asc=True)
    compiled = _compiled(stmt)
    assert "ORDER BY" in compiled
    assert "spotify_song.title COLLATE" in compiled


def test_sql_expression_is_rejected():
    """The injection payload from the report never reaches the statement."""
    payload = ("case when (select substr(title,1,6) from spotify_song)"
               "='Secret' then title else album_uuid end")
    assert database.resolve_order_column(payload) is None
    stmt = database.limit_and_order_stmt(
        select(database.dbms.spotify_song.c.title), order=payload)
    compiled = _compiled(stmt)
    assert "ORDER BY" not in compiled
    assert "substr" not in compiled


def test_unknown_table_or_column_is_rejected():
    """Only columns the schema actually has are sortable."""
    assert database.resolve_order_column("no_such_table.title") is None
    assert database.resolve_order_column("spotify_song.no_such_column") is None


def test_trailing_sql_is_rejected():
    """Anything other than a bare ``table.column`` is refused."""
    assert database.resolve_order_column("spotify_song.title desc") is None
    assert database.resolve_order_column("spotify_song.title, (select 1)") is None
    assert database.resolve_order_column("spotify_song.title; drop table user") is None
    assert database.resolve_order_column("") is None
    assert database.resolve_order_column(None) is None
