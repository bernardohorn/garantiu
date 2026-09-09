import sqlite3

import pytest

from garantiu.release_history import (
    get_release_history,
    record_release_outcome,
    record_release_score,
)


def test_empty_and_scores_join_latest_outcomes(tmp_path):
    db = str(tmp_path / "releases.db")
    assert get_release_history(db) == []
    assert record_release_score(db, "v1", 58) == 1
    record_release_outcome(db, "v1", "ok")
    record_release_score(db, "v2", 85)
    history = get_release_history(db)
    assert [r["release"] for r in history] == ["v2", "v1"]
    assert history[0]["score"] == 85
    assert history[0]["outcome"] is None
    assert history[1]["outcome"] == "ok"


def test_reanalysis_is_one_row_and_timestamp_ties_use_ids(tmp_path):
    db = str(tmp_path / "releases.db")
    record_release_score(db, "v1", 58)
    record_release_score(db, "v2", 20)
    record_release_score(db, "v1", 85)
    record_release_outcome(db, "v1", "ok")
    record_release_outcome(db, "v1", "falhou")
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE release_scores SET computed_at = '2026-01-01'")
        conn.execute("UPDATE release_outcomes SET recorded_at = '2026-01-01'")
    history = get_release_history(db)
    assert [r["release"] for r in history] == ["v1", "v2"]
    assert history[0] == {
        "release": "v1", "score": 85, "computed_at": "2026-01-01", "outcome": "falhou"
    }


def test_repository_scope_and_unknown_release(tmp_path):
    db = str(tmp_path / "releases.db")
    record_release_score(db, "v1", 10, repo_key="one")
    with pytest.raises(ValueError, match="recorded score"):
        record_release_outcome(db, "v1", "ok", repo_key="two")
    record_release_score(db, "v1", 90, repo_key="two")
    record_release_outcome(db, "v1", "falhou", repo_key="two")
    assert get_release_history(db) == []
    assert get_release_history(db, repo_key="one")[0]["outcome"] is None
    assert get_release_history(db, repo_key="one")[0]["score"] == 10
    assert get_release_history(db, repo_key="two")[0]["outcome"] == "falhou"
    with pytest.raises(ValueError, match="recorded score"):
        record_release_outcome(db, "missing", "ok")


@pytest.mark.parametrize("score", [-1, 101, float("nan"), float("inf"), "20", True])
def test_invalid_score_rejected(tmp_path, score):
    db = str(tmp_path / "releases.db")
    with pytest.raises(ValueError):
        record_release_score(db, "v1", score)
    assert get_release_history(db) == []


@pytest.mark.parametrize("release", ["", "   ", None])
def test_empty_release_rejected(tmp_path, release):
    db = str(tmp_path / "releases.db")
    with pytest.raises(ValueError):
        record_release_score(db, release, 20)
    with pytest.raises(ValueError):
        record_release_outcome(db, release, "ok")


def test_invalid_outcome_rejected(tmp_path):
    with pytest.raises(ValueError, match="outcome"):
        record_release_outcome(str(tmp_path / "releases.db"), "v1", "talvez")
