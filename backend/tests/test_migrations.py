"""Upgrading a v1 database must add the new columns and tables without losing data."""

import sqlite3

import pytest
from sqlalchemy import inspect
from sqlmodel import create_engine

import db
import migrations

# The exact schema the v1 MVP created (copied from a real v1 tracker.db).
V1_SCHEMA = """
CREATE TABLE problem (
    id INTEGER NOT NULL, title_slug VARCHAR NOT NULL, title VARCHAR NOT NULL,
    difficulty VARCHAR NOT NULL, topics VARCHAR NOT NULL, url VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_problem_title_slug ON problem (title_slug);
CREATE TABLE solve (
    id INTEGER NOT NULL, problem_id INTEGER NOT NULL, solved_at DATETIME NOT NULL,
    solved_date DATE NOT NULL, source VARCHAR NOT NULL, time_spent_min INTEGER,
    confidence INTEGER, notes VARCHAR NOT NULL, needs_review BOOLEAN NOT NULL,
    PRIMARY KEY (id), UNIQUE (problem_id, solved_date),
    FOREIGN KEY(problem_id) REFERENCES problem (id)
);
INSERT INTO problem VALUES
    (1, 'two-sum', 'Two Sum', 'Easy', '["Array", "Hash Table"]',
     'https://leetcode.com/problems/two-sum/');
INSERT INTO solve VALUES
    (1, 1, '2026-10-07 14:00:00', '2026-10-07', 'sync', 20, 2, 'used a dict', 0),
    (2, 1, '2026-10-09 03:14:21', '2026-10-08', 'manual', NULL, NULL, '', 1);
"""


def make_engine(path):
    return create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})


@pytest.fixture
def v1_engine(tmp_path, monkeypatch):
    path = tmp_path / "v1.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(V1_SCHEMA)
    engine = make_engine(path)
    monkeypatch.setattr(db, "engine", engine)
    return engine


def columns(engine, table):
    return {column["name"] for column in inspect(engine).get_columns(table)}


def stored_version(engine):
    with engine.connect() as conn:
        return conn.exec_driver_sql("SELECT version FROM schema_version").scalar()


def test_upgrades_v1_database_and_keeps_rows(v1_engine):
    db.create_db_and_tables()  # the real startup path

    assert {"approach", "code", "language", "time_complexity", "space_complexity"} <= columns(
        v1_engine, "solve"
    )
    assert stored_version(v1_engine) == migrations.LATEST_VERSION

    with v1_engine.connect() as conn:
        rows = conn.exec_driver_sql(
            "SELECT id, notes, confidence, language, approach FROM solve ORDER BY id"
        ).all()
    assert rows == [(1, "used a dict", 2, "python3", None), (2, "", None, "python3", None)]


def test_running_twice_is_a_no_op(v1_engine):
    db.create_db_and_tables()
    assert migrations.run_migrations(v1_engine) == 0
    db.create_db_and_tables()  # a second startup doesn't fail either
    assert stored_version(v1_engine) == migrations.LATEST_VERSION


def test_upgraded_schema_matches_fresh_schema(v1_engine, tmp_path, monkeypatch):
    db.create_db_and_tables()

    fresh = make_engine(tmp_path / "fresh.db")
    monkeypatch.setattr(db, "engine", fresh)
    db.create_db_and_tables()

    tables = set(inspect(fresh).get_table_names())
    assert tables == set(inspect(v1_engine).get_table_names())
    for table in tables:
        assert columns(v1_engine, table) == columns(fresh, table), table


def test_fresh_database_is_stamped_without_running_migrations(tmp_path, monkeypatch):
    fresh = make_engine(tmp_path / "fresh.db")
    monkeypatch.setattr(db, "engine", fresh)
    db.create_db_and_tables()

    assert stored_version(fresh) == migrations.LATEST_VERSION
    assert migrations.run_migrations(fresh) == 0


def test_failed_migration_is_rolled_back(v1_engine, monkeypatch):
    def broken(conn):
        conn.execute("ALTER TABLE solve ADD COLUMN half_done TEXT")
        raise RuntimeError("boom")

    monkeypatch.setattr(migrations, "MIGRATIONS", [broken])

    with pytest.raises(RuntimeError, match="boom"):
        migrations.run_migrations(v1_engine)

    assert "half_done" not in columns(v1_engine, "solve")
    assert stored_version(v1_engine) == 0
