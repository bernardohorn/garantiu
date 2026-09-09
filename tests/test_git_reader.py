import pytest

from garantiu.git_reader import get_changed_files
from tests.conftest import init_repo


@pytest.fixture
def sample_repo(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    repo = init_repo(repo_path)
    (repo_path / "checkout").mkdir()
    gateway = repo_path / "checkout" / "gateway.py"
    gateway.write_text("def pay():\n    pass\n")
    repo.index.add(["checkout/gateway.py"])
    repo.index.commit("initial commit")
    repo.create_tag("v1.0.0")

    gateway.write_text("def pay():\n    pass\n\ndef refund():\n    pass\n")
    repo.index.add(["checkout/gateway.py"])
    repo.index.commit("add refund")
    return str(repo_path)


def test_get_changed_files_detects_module_and_lines(sample_repo):
    changes = get_changed_files(sample_repo, "v1.0.0", "HEAD")
    assert len(changes) == 1
    assert changes[0]["path"] == "checkout/gateway.py"
    assert changes[0]["module"] == "checkout"
    assert changes[0]["lines_added"] == 3
    assert changes[0]["lines_removed"] == 0


def test_get_changed_files_resolves_module_on_rename_same_filename(tmp_path):
    repo_path = tmp_path / "repo3"
    repo_path.mkdir()
    repo = init_repo(repo_path)
    (repo_path / "checkout").mkdir()
    gateway = repo_path / "checkout" / "gateway.py"
    gateway.write_text("def pay():\n    pass\n")
    repo.index.add(["checkout/gateway.py"])
    repo.index.commit("initial commit")

    (repo_path / "billing").mkdir()
    repo.index.move(["checkout/gateway.py", "billing/gateway.py"])
    repo.index.commit("move gateway to billing")

    changes = get_changed_files(str(repo_path), "HEAD~1", "HEAD")
    assert len(changes) == 1
    assert changes[0]["module"] == "billing"
    assert changes[0]["path"] == "billing/gateway.py"


def test_get_changed_files_resolves_module_on_rename_different_filename(tmp_path):
    repo_path = tmp_path / "repo4"
    repo_path.mkdir()
    repo = init_repo(repo_path)
    (repo_path / "checkout").mkdir()
    gateway = repo_path / "checkout" / "gateway.py"
    gateway.write_text("def pay():\n    pass\n\ndef refund():\n    pass\n")
    repo.index.add(["checkout/gateway.py"])
    repo.index.commit("initial commit")

    (repo_path / "billing").mkdir()
    repo.index.move(["checkout/gateway.py", "billing/pay.py"])
    repo.index.commit("move and rename gateway to billing/pay")

    changes = get_changed_files(str(repo_path), "HEAD~1", "HEAD")
    assert len(changes) == 1
    assert changes[0]["module"] == "billing"
    assert changes[0]["path"] == "billing/pay.py"


def test_get_changed_files_uses_filename_as_module_at_repo_root(tmp_path):
    repo_path = tmp_path / "repo2"
    repo_path.mkdir()
    repo = init_repo(repo_path)
    f = repo_path / "README.md"
    f.write_text("v1")
    repo.index.add(["README.md"])
    repo.index.commit("initial")
    repo.create_tag("v1.0.0")
    f.write_text("v1\nv2")
    repo.index.add(["README.md"])
    repo.index.commit("update readme")

    changes = get_changed_files(str(repo_path), "v1.0.0", "HEAD")
    assert changes[0]["module"] == "README.md"
