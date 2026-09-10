from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from garantiu.release_history import get_release_history
from garantiu.ui import BRAND_FULL_PATH, BRAND_SYMBOL_PATH, BRAND_WORDMARK_PATH
from tests.conftest import init_repo
from tests.test_repository_source import remote_fixture


def select_fixture_reports(at):
    root = Path(__file__).resolve().parents[1] / "sample_data"
    at.text_input[3].set_value(str(root / "sample_junit.xml"))
    at.text_input[4].set_value(str(root / "incidents.csv"))
    at.text_input[5].set_value(str(root / "incident_details.csv"))


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setenv("GARANTIU_DATA_DIR", str(tmp_path / "data"))


@pytest.fixture
def analyzed_app(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    repo = init_repo(repo_path)
    (repo_path / "checkout").mkdir()
    source = repo_path / "checkout/gateway.py"
    source.write_text("v1\n", encoding="utf-8")
    repo.index.add(["checkout/gateway.py"])
    repo.index.commit("initial")
    source.write_text("v1\nv2\n", encoding="utf-8")
    repo.index.add(["checkout/gateway.py"])
    repo.index.commit("fix: gateway")
    repo.close()
    at = AppTest.from_file("../app.py", default_timeout=15).run()
    at.text_input[0].set_value(str(repo_path)).run()
    select_fixture_reports(at)
    at.button[0].click().run()
    assert not at.exception
    assert not at.error
    return at


def test_app_loads_without_exceptions():
    at = AppTest.from_file("../app.py", default_timeout=15)
    at.run()
    assert not at.exception


def test_full_pipeline_runs_end_to_end_and_populates_risk_overview():
    """
    Exercises the real analysis pipeline exactly as app.py composes it:
    clicking "Analisar mudanças" on the default "Conectar Release" screen
    (with its default input values, which point at this actual git repo and
    the real sample JUnit/incidents files) must run get_changed_files ->
    build_bug_history -> parse_junit_report -> test_health_by_module ->
    load_incidents -> score_modules -> score_release without raising, store
    the result in session_state, and make it visible on the "Visão Geral do
    Risco" screen. No mocking: this is the only test that runs the modules
    wired together the way the app actually wires them.
    """
    at = AppTest.from_file("../app.py", default_timeout=15)
    at.run()
    assert not at.exception

    # Exercise explicit report ingestion; sample files are never defaults.
    select_fixture_reports(at)
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state.analysis is not None
    assert at.session_state.analysis["release"]["top_module"] is not None

    at.sidebar.radio[0].set_value("Visão Geral do Risco").run()
    assert not at.exception
    assert len(at.metric) == 1
    assert at.metric[0].value != ""
    assert at.metric[0].value.endswith("/100")


def test_risk_overview_primary_action_opens_manual_guide(analyzed_app):
    at = analyzed_app
    at.sidebar.radio[0].set_value("Visão Geral do Risco").run()
    assert at.button[0].label == "Preparar teste manual"

    at.button[0].click().run()

    assert at.sidebar.radio[0].value == "Roteiro de Teste Manual"
    assert at.title[0].value == "Roteiro de teste manual"


def test_all_seven_screens_without_analysis():
    at = AppTest.from_file("../app.py").run()
    screens = list(at.sidebar.radio[0].options)
    assert len(screens) == 7
    for screen in screens:
        at.sidebar.radio[0].set_value(screen).run()
        assert not at.exception
        assert not at.error


def test_populated_screens_decision_and_outcome_persist(analyzed_app, tmp_path):
    at = analyzed_app
    analysis = at.session_state.analysis
    assert analysis["module_scores"][0]["module"] == "checkout"
    for screen in list(at.sidebar.radio[0].options)[1:]:
        at.sidebar.radio[0].set_value(screen).run()
        assert not at.exception
        assert not at.error
        assert at.title

    at.sidebar.radio[0].set_value("Suíte Automatizada Priorizada").run()
    assert at.table[0].value.iloc[0]["Teste"] == "test_pagamento_recusado"
    at.sidebar.radio[0].set_value("Detalhe do Módulo").run()
    assert at.selectbox[0].value == "checkout"
    assert at.table[1].value.iloc[0]["message"] == "fix: gateway"
    assert len(at.table[2].value) == 2

    at.sidebar.radio[0].set_value("Decisão de Publicação").run()
    assert at.button[0].disabled
    at.text_input[0].set_value("   ").run()
    assert at.button[0].disabled
    at.text_input[0].set_value("Pessoa de teste").run()
    at.button[0].click().run()
    assert not at.exception
    assert at.table[0].value.iloc[0]["decision"] == "publicar"
    at.button[1].click().run()
    assert at.table[0].value.iloc[0]["decision"] == "cancelar"

    at.sidebar.radio[0].set_value("Histórico & Tendências").run()
    at.radio(key="outcome").set_value("falhou")
    at.button[0].click().run()
    assert not at.exception
    assert at.table[0].value.iloc[0]["outcome"] == "falhou"
    history = get_release_history(
        str(tmp_path / "data/garantiu_release_history.db"),
        repo_key=analysis["repo_path"],
    )
    assert len(history) == 1
    assert history[0]["outcome"] == "falhou"
    # A new browser session can read the same persisted history.
    fresh = AppTest.from_file("../app.py").run()
    fresh.sidebar.radio[0].set_value("Histórico & Tendências").run()
    fresh.text_input[0].set_value(analysis["repo_path"]).run()
    assert fresh.table[0].value.iloc[0]["outcome"] == "falhou"


def test_manual_guide_note_field_is_session_only(analyzed_app):
    at = analyzed_app
    at.sidebar.radio[0].set_value("Roteiro de Teste Manual").run()
    assert len(at.text_area) == 1
    at.text_area[0].set_value("Atenção ao fluxo de desconto.").run()
    assert at.session_state["nota_dev_checkout"] == "Atenção ao fluxo de desconto."

    fresh = AppTest.from_file("../app.py", default_timeout=15).run()
    assert "nota_dev_checkout" not in fresh.session_state


def test_repeated_analysis_uses_real_test_flips(analyzed_app, tmp_path):
    at = analyzed_app
    repo_path = at.session_state.analysis["repo_path"]
    initial_score = at.session_state.analysis["release"]["score"]
    root = Path(__file__).resolve().parents[1]
    report = tmp_path / "next.xml"
    report.write_text(
        (root / "sample_data/sample_junit.xml").read_text(encoding="utf-8")
        .replace('<testcase classname="checkout.test_gateway" '
                 'name="test_pagamento_aprovado" time="0.01"/>',
                 '<testcase classname="checkout.test_gateway" '
                 'name="test_pagamento_aprovado" time="0.01">'
                 '<failure/></testcase>'),
        encoding="utf-8",
    )
    at.text_input[3].set_value(str(report))
    at.button[0].click().run()
    assert not at.exception
    assert not at.error
    assert at.session_state.analysis["flakiness"]["checkout"] == 50.0
    assert at.session_state.analysis["release"]["score"] > initial_score
    history = get_release_history(
        str(tmp_path / "data/garantiu_release_history.db"), repo_key=repo_path,
    )
    assert len(history) == 1


def test_empty_diff_and_empty_report_are_navigable(analyzed_app, tmp_path):
    at = analyzed_app
    original_release = at.session_state.analysis["release_name"]
    report = tmp_path / "empty.xml"
    report.write_text("<testsuites/>", encoding="utf-8")
    at.text_input[1].set_value("HEAD")
    at.text_input[3].set_value(str(report))
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state.analysis["module_scores"] == []
    assert at.session_state.analysis["release_name"] != original_release
    history = get_release_history(
        str(tmp_path / "data/garantiu_release_history.db"),
        repo_key=at.session_state.analysis["repo_path"],
    )
    assert len(history) == 2
    for screen in list(at.sidebar.radio[0].options)[1:]:
        at.sidebar.radio[0].set_value(screen).run()
        assert not at.exception
        assert not at.error


@pytest.mark.parametrize("field,value", [
    (0, "missing-repository"), (1, "missing-ref"),
    (3, "missing-report.xml"), (4, "missing-incidents.csv"),
    (5, "missing-details.csv"),
])
def test_invalid_inputs_show_error_without_recording(field, value, tmp_path):
    at = AppTest.from_file("../app.py", default_timeout=15).run()
    at.text_input[field].set_value(value)
    at.button[0].click().run()
    assert not at.exception
    assert at.error
    assert at.session_state.analysis is None
    assert not (tmp_path / "data/garantiu_test_history.db").exists()


def test_failed_reanalysis_clears_stale_analysis(analyzed_app):
    at = analyzed_app
    at.text_input[3].set_value("missing-report.xml")
    at.button[0].click().run()
    assert not at.exception
    assert at.error
    assert at.session_state.analysis is None


def test_default_analysis_has_no_fictitious_test_results(tmp_path):
    at = AppTest.from_file("../app.py", default_timeout=15).run()
    assert all(not field.value for field in at.text_input[3:6])
    at.button[0].click().run()
    assert not at.exception
    assert not at.error
    assert at.session_state.analysis["test_results"] == []
    assert at.session_state.analysis["flakiness"] == {}
    assert not (tmp_path / "data/garantiu_test_history.db").exists()
    at.sidebar.radio[0].set_value("Suíte Automatizada Priorizada").run()
    assert not at.table
    assert "Nenhum relatório" in at.info[0].value


def test_brand_assets_are_present_and_rendered_in_all_three_variants():
    assert BRAND_FULL_PATH.is_file()
    assert BRAND_SYMBOL_PATH.is_file()
    assert BRAND_WORDMARK_PATH.is_file()

    at = AppTest.from_file("../app.py", default_timeout=15).run()

    assert not at.exception
    html = "\n".join(item.value for item in at.markdown)
    sidebar_html = "\n".join(item.value for item in at.sidebar.markdown)
    assert 'class="page-brand-symbol"' in html
    assert 'class="brand-full-crop"' in sidebar_html
    assert 'class="sidebar-footer"' in sidebar_html
    assert '# <div class="brand-lockup"' not in sidebar_html
    assert not at.error


def test_documentation_only_interval_does_not_inflate_release_risk(tmp_path):
    repo_path = tmp_path / "docs-only"
    repo_path.mkdir()
    repo = init_repo(repo_path)
    readme = repo_path / "README.md"
    readme.write_text("initial\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("initial")
    readme.write_text("initial\nmore docs\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("docs: update readme")
    repo.close()

    at = AppTest.from_file("../app.py", default_timeout=15).run()
    at.text_input[0].set_value(str(repo_path)).run()
    at.button[0].click().run()

    assert not at.exception
    assert not at.error
    assert at.session_state.analysis["changed_files"] == []
    assert len(at.session_state.analysis["documentation_files"]) == 1
    assert at.session_state.analysis["release"]["score"] == 0
    assert any("não influenciaram" in item.value for item in at.info)
    assert any("não contém mudanças de produto" in item.value for item in at.warning)


def test_switching_repository_clears_report_and_stale_analysis(analyzed_app):
    at = analyzed_app
    assert at.text_input[3].value
    at.text_input[0].set_value("https://github.com/other/project").run()
    assert at.session_state.analysis is None
    assert not at.text_input[3].value
    assert not at.text_input[4].value
    at.sidebar.radio[0].set_value("Suíte Automatizada Priorizada").run()
    assert not at.table


def test_repository_input_survives_navigation_between_screens():
    at = AppTest.from_file("../app.py").run()
    repository = "https://github.com/owner/persistent-project"
    at.text_input[0].set_value(repository).run()

    at.sidebar.radio[0].set_value("Visão Geral do Risco").run()
    assert at.session_state.repository_source == repository

    at.sidebar.radio[0].set_value("Histórico & Tendências").run()
    assert at.text_input[0].value == repository

    at.sidebar.radio[0].set_value("Conectar Release").run()
    assert at.text_input[0].value == repository


def test_report_in_github_commit_populates_actual_suite(remote_fixture):
    upstream, _ = remote_fixture
    from git import Repo
    with Repo(upstream) as repo:
        (upstream / "results.xml").write_text(
            '<testsuite><testcase classname="checkout.pay" name="test_real" '
            'time="0.25"><failure/></testcase></testsuite>', encoding="utf-8",
        )
        repo.index.add(["results.xml"])
        repo.index.commit("test report")
    at = AppTest.from_file("../app.py", default_timeout=15).run()
    at.text_input[0].set_value("https://github.com/owner/project").run()
    at.text_input[1].set_value("v1")
    at.text_input[3].set_value("repo:results.xml")
    at.button[0].click().run()
    assert not at.exception
    assert not at.error
    at.sidebar.radio[0].set_value("Suíte Automatizada Priorizada").run()
    assert at.table[0].value["Teste"].tolist() == ["test_real"]
    assert at.table[0].value.iloc[0]["Status"] == "failed"
    assert any("repo:results.xml" in caption.value for caption in at.caption)


def test_github_analysis_all_screens_and_persistent_url_history(remote_fixture):
    _, calls = remote_fixture
    at = AppTest.from_file("../app.py", default_timeout=15).run()
    at.text_input[0].set_value("https://github.com/Owner/Project.git")
    at.text_input[1].set_value("v1")
    at.text_input[2].set_value("release/test")
    at.button[0].click().run()
    assert not at.exception
    assert not at.error
    assert at.session_state.analysis["repo_path"] == "https://github.com/owner/project"
    assert at.session_state.analysis["changed_files"][0]["path"] == "checkout/pay.py"
    for screen in list(at.sidebar.radio[0].options)[1:]:
        at.sidebar.radio[0].set_value(screen).run()
        assert not at.exception
        assert not at.error
    at.radio(key="outcome").set_value("ok")
    at.button[0].click().run()
    assert at.table[0].value.iloc[0]["outcome"] == "ok"
    fresh = AppTest.from_file("../app.py").run()
    fresh.sidebar.radio[0].set_value("Histórico & Tendências").run()
    fresh.text_input[0].set_value("https://github.com/OWNER/PROJECT.git/").run()
    assert not fresh.error
    assert fresh.table[0].value.iloc[0]["outcome"] == "ok"
    assert len(calls) == 1  # Reading persisted history never downloads again.


def test_invalid_github_url_shows_error_without_analysis():
    at = AppTest.from_file("../app.py").run()
    at.text_input[0].set_value("https://github.com/owner/project/tree/main")
    at.button[0].click().run()
    assert not at.exception
    assert at.error
    assert at.session_state.analysis is None
