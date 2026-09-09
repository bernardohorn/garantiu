"""Store release risk scores and subsequently observed outcomes."""

import math
import sqlite3
from contextlib import closing
from datetime import datetime, timezone


def init_db(db_path: str) -> None:
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS release_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_key TEXT NOT NULL DEFAULT '',
                release TEXT NOT NULL,
                score REAL NOT NULL CHECK(score >= 0 AND score <= 100),
                computed_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS release_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_key TEXT NOT NULL DEFAULT '',
                release TEXT NOT NULL,
                outcome TEXT NOT NULL CHECK(outcome IN ('ok', 'falhou')),
                recorded_at TEXT NOT NULL
            )"""
        )


def _validate_identity(release: str, repo_key: str) -> None:
    if not isinstance(release, str) or not release.strip():
        raise ValueError("release must be a nonempty string")
    if not isinstance(repo_key, str):
        raise ValueError("repo_key must be a string")


def record_release_score(
    db_path: str, release: str, score: float, *, repo_key: str = ""
) -> int:
    _validate_identity(release, repo_key)
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(score)
        or not 0 <= score <= 100
    ):
        raise ValueError("score must be a finite number between 0 and 100")
    init_db(db_path)
    with closing(sqlite3.connect(db_path)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO release_scores (repo_key, release, score, computed_at) "
            "VALUES (?, ?, ?, ?)",
            (repo_key, release, score, datetime.now(timezone.utc).isoformat()),
        )
        return cursor.lastrowid


def record_release_outcome(
    db_path: str, release: str, outcome: str, *, repo_key: str = ""
) -> int:
    """Record 'ok' or 'falhou' for an existing scored release."""
    _validate_identity(release, repo_key)
    if outcome not in ("ok", "falhou"):
        raise ValueError("outcome must be 'ok' or 'falhou'")
    init_db(db_path)
    with closing(sqlite3.connect(db_path)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO release_outcomes (repo_key, release, outcome, recorded_at) "
            "SELECT ?, ?, ?, ? WHERE EXISTS "
            "(SELECT 1 FROM release_scores WHERE repo_key = ? AND release = ?)",
            (repo_key, release, outcome, datetime.now(timezone.utc).isoformat(),
             repo_key, release),
        )
        if cursor.rowcount != 1:
            raise ValueError("release must have a recorded score in this repository")
        return cursor.lastrowid


def get_release_history(db_path: str, *, repo_key: str = "") -> list[dict]:
    """Return one latest score and outcome per release, newest score first."""
    if not isinstance(repo_key, str):
        raise ValueError("repo_key must be a string")
    init_db(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT s.release, s.score, s.computed_at,
                (SELECT o.outcome FROM release_outcomes o
                 WHERE o.repo_key = s.repo_key AND o.release = s.release
                 ORDER BY o.recorded_at DESC, o.id DESC LIMIT 1) AS outcome
            FROM release_scores s
            WHERE s.repo_key = ? AND s.id = (
                SELECT latest.id FROM release_scores latest
                WHERE latest.repo_key = s.repo_key AND latest.release = s.release
                ORDER BY latest.computed_at DESC, latest.id DESC LIMIT 1
            )
            ORDER BY s.computed_at DESC, s.id DESC""", (repo_key,)
        ).fetchall()
    return [dict(row) for row in rows]
