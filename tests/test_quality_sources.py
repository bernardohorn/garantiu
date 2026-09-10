import git
import pytest

from garantiu.quality_sources import discover_quality_sources
from tests.conftest import init_repo


def test_discovers_quality_files_by_content_in_local_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    with init_repo(project) as repo:
        (project / "src.py").write_text("value = 1\n", encoding="utf-8")
        repo.index.add(["src.py"])
        repo.index.commit("initial")
    reports = project / "reports"
    reports.mkdir()
    junit = reports / "custom.xml"
    counts = reports / "operational.csv"
    details = reports / "events.csv"
    junit.write_text("<testsuite><testcase name='ok'/></testsuite>", encoding="utf-8")
    counts.write_text("module,incident_count\ncheckout,2\n", encoding="utf-8")
    details.write_text(
        "module,description,date\ncheckout,outage,2026-09-10\n",
        encoding="utf-8",
    )
    (reports / "other.xml").write_text("<project/>", encoding="utf-8")

    found = discover_quality_sources(str(project))

    assert found == {
        "junit": [str(junit.resolve())],
        "incident_counts": [str(counts.resolve())],
        "incident_details": [str(details.resolve())],
    }


def test_bare_repository_returns_repo_locations_and_prefers_known_names(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    with init_repo(project) as repo:
        (project / "reports").mkdir()
        (project / "reports/results.xml").write_text(
            "<testsuite/>", encoding="utf-8",
        )
        (project / "z.xml").write_text("<testsuite/>", encoding="utf-8")
        repo.index.add(["reports/results.xml", "z.xml"])
        repo.index.commit("reports")
    bare = tmp_path / "project.git"
    with git.Repo.clone_from(project, bare, bare=True):
        pass

    found = discover_quality_sources(str(bare))

    assert found["junit"] == ["repo:reports/results.xml", "repo:z.xml"]


@pytest.mark.parametrize("directory_name", [".venv", "sample_data", "fixtures", "garantiu-junit"])
def test_ignores_non_production_candidate_directories(tmp_path, directory_name):
    project = tmp_path / "project"
    project.mkdir()
    with init_repo(project) as repo:
        (project / "src.py").write_text("value = 1\n", encoding="utf-8")
        repo.index.add(["src.py"])
        repo.index.commit("initial")
    ignored = project / directory_name
    ignored.mkdir()
    (ignored / "junit.xml").write_text("<testsuite/>", encoding="utf-8")

    assert discover_quality_sources(str(project))["junit"] == []
