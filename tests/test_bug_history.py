import git
import pytest

from garantiu.bug_history import build_bug_history, get_bug_fix_commits


@pytest.fixture
def repo_with_bug_fixes(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    repo = git.Repo.init(repo_path)
    (repo_path / "checkout").mkdir()
    f = repo_path / "checkout" / "gateway.py"

    f.write_text("v1")
    repo.index.add(["checkout/gateway.py"])
    repo.index.commit("initial commit")

    f.write_text("v2")
    repo.index.add(["checkout/gateway.py"])
    repo.index.commit("fix: corrige calculo do gateway")

    f.write_text("v3")
    repo.index.add(["checkout/gateway.py"])
    repo.index.commit("add new feature")

    f.write_text("v4")
    repo.index.add(["checkout/gateway.py"])
    repo.index.commit("fixes bug in refund flow")

    return str(repo_path)


def test_get_bug_fix_commits_filters_by_message(repo_with_bug_fixes):
    commits = get_bug_fix_commits(repo_with_bug_fixes)
    assert len(commits) == 2
    messages = [c["message"] for c in commits]
    assert any("corrige" in m for m in messages)
    assert any("fixes bug" in m for m in messages)


def test_build_bug_history_counts_per_file(repo_with_bug_fixes):
    history = build_bug_history(repo_with_bug_fixes)
    assert history["checkout/gateway.py"] == 2
