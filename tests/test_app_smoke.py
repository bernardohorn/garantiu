from streamlit.testing.v1 import AppTest


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
