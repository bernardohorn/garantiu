from pathlib import Path

import git
import pytest
from streamlit.testing.v1 import AppTest

from garantiu.release_history import get_release_history


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setenv("GARANTIU_DATA_DIR", str(tmp_path / "data"))


@pytest.fixture
def analyzed_app(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    repo = git.Repo.init(repo_path)
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
    at.text_input[0].set_value(str(repo_path))
    at.button[0].click().run()
    assert not at.exception
    assert not at.error
    return at


def test_app_loads_without_exceptions():
    at = AppTest.from_file("../app.py")
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
    at = AppTest.from_file("../app.py")
    at.run()
    assert not at.exception

    # Default inputs on "Conectar Release" already point at this repo
    # (repo_path=".") and its real HEAD~1..HEAD diff, plus the real sample
    # JUnit/incidents files. Just click the analysis button.
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state.analysis is not None
    assert at.session_state.analysis["release"]["top_module"] is not None

    at.sidebar.radio[0].set_value("Visão Geral do Risco").run()
    assert not at.exception
    assert len(at.metric) == 1
    assert at.metric[0].value != ""
    assert at.metric[0].value.endswith("/100")


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
