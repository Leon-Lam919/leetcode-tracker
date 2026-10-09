"""Small hand-rolled schema migrations for SQLite.

`SQLModel.metadata.create_all` creates missing *tables*, but it never adds new
*columns* to a table that already exists. The owner's database already has data,
so each schema change is written as a numbered migration (plain SQL) instead.

How it works:
- The `schema_version` table holds one row: the number of the last migration applied.
- `MIGRATIONS` is an ordered list. Migration N is `MIGRATIONS[N - 1]`.
- On startup, every migration newer than the stored version runs inside its own
  transaction, and the version is bumped in that same transaction. If a migration
  fails, it is rolled back completely and the app doesn't start.

This is the same idea as Alembic (SQLAlchemy's migration tool), minus the extras.
"""

import sqlite3
from collections.abc import Callable

from loguru import logger
from sqlalchemy import Engine, inspect

# ---------------------------------------------------------------------------
# Migrations. Never edit or reorder one that has shipped; add a new one instead.
# ---------------------------------------------------------------------------


def add_solution_fields(conn: sqlite3.Connection) -> None:
    """v2 feature 4: write down how you solved it."""
    conn.execute("ALTER TABLE solve ADD COLUMN approach TEXT")
    conn.execute("ALTER TABLE solve ADD COLUMN code TEXT")
    conn.execute("ALTER TABLE solve ADD COLUMN language VARCHAR DEFAULT 'python3'")
    conn.execute("ALTER TABLE solve ADD COLUMN time_complexity VARCHAR")
    conn.execute("ALTER TABLE solve ADD COLUMN space_complexity VARCHAR")


def add_review_table(conn: sqlite3.Connection) -> None:
    """v2 feature 1: spaced-repetition schedule, one row per problem."""
    conn.execute(
        """
        CREATE TABLE review (
            id INTEGER NOT NULL,
            problem_id INTEGER NOT NULL,
            interval_index INTEGER NOT NULL,
            next_review_date DATE,
            last_reviewed_date DATE NOT NULL,
            last_confidence INTEGER,
            PRIMARY KEY (id),
            UNIQUE (problem_id),
            FOREIGN KEY(problem_id) REFERENCES problem (id)
        )
        """
    )
    conn.execute("CREATE INDEX ix_review_next_review_date ON review (next_review_date)")
    # Backfill: every problem already solved gets a review the day after its latest solve.
    conn.execute(
        """
        INSERT INTO review
            (problem_id, interval_index, next_review_date, last_reviewed_date, last_confidence)
        SELECT
            latest.problem_id,
            0,
            date(latest.last_date, '+1 day'),
            latest.last_date,
            (SELECT s.confidence FROM solve s
             WHERE s.problem_id = latest.problem_id AND s.solved_date = latest.last_date)
        FROM (SELECT problem_id, MAX(solved_date) AS last_date FROM solve GROUP BY problem_id)
            AS latest
        """
    )


def add_pattern_tables(conn: sqlite3.Connection) -> None:
    """v2 feature 2: pattern checklists. Rows are seeded on startup, not here."""
    conn.execute(
        """
        CREATE TABLE pattern_list (
            id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            PRIMARY KEY (id),
            UNIQUE (name)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE pattern_problem (
            id INTEGER NOT NULL,
            list_id INTEGER NOT NULL,
            slug VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            difficulty VARCHAR NOT NULL,
            pattern VARCHAR NOT NULL,
            position INTEGER NOT NULL,
            PRIMARY KEY (id),
            UNIQUE (list_id, slug),
            FOREIGN KEY(list_id) REFERENCES pattern_list (id)
        )
        """
    )
    conn.execute("CREATE INDEX ix_pattern_problem_list_id ON pattern_problem (list_id)")


Migration = Callable[[sqlite3.Connection], None]

MIGRATIONS: list[Migration] = [
    add_solution_fields,  # 1
    add_review_table,  # 2
    add_pattern_tables,  # 3
]

LATEST_VERSION = len(MIGRATIONS)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def is_fresh_database(engine: Engine) -> bool:
    """True if the app has never created its tables in this database."""
    return not inspect(engine).has_table("problem")


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    if conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == 0:
        conn.execute("INSERT INTO schema_version (version) VALUES (0)")  # a v1 database


def get_version(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT version FROM schema_version").fetchone()[0]


def _with_raw_connection(engine: Engine, work: Callable[[sqlite3.Connection], int]) -> int:
    """Run `work` on the underlying sqlite3 connection with manual transactions.

    Python's sqlite3 module normally commits on its own before ALTER/CREATE
    statements. Setting isolation_level to None turns that off, so our own
    BEGIN ... COMMIT really covers the schema changes too.
    """
    pooled = engine.raw_connection()
    conn = pooled.driver_connection
    old_isolation = conn.isolation_level
    conn.isolation_level = None
    try:
        return work(conn)
    finally:
        conn.isolation_level = old_isolation
        pooled.close()


def run_migrations(engine: Engine) -> int:
    """Apply every pending migration. Returns how many ran (0 if already up to date)."""

    def work(conn: sqlite3.Connection) -> int:
        _ensure_version_table(conn)
        version = get_version(conn)
        applied = 0
        for number, migration in enumerate(MIGRATIONS, start=1):
            if number <= version:
                continue
            conn.execute("BEGIN")
            try:
                migration(conn)
                conn.execute("UPDATE schema_version SET version = ?", (number,))
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                logger.error("Migration {} ({}) failed; rolled back", number, migration.__name__)
                raise
            logger.info("Applied migration {}: {}", number, migration.__name__)
            applied += 1
        return applied

    return _with_raw_connection(engine, work)


def stamp_latest(engine: Engine) -> None:
    """Mark a brand-new database as fully up to date.

    create_all() just built every table from the current models, so the
    migrations' changes are already there and must not run again.
    """

    def work(conn: sqlite3.Connection) -> int:
        _ensure_version_table(conn)
        conn.execute("UPDATE schema_version SET version = ?", (LATEST_VERSION,))
        return 0

    _with_raw_connection(engine, work)
