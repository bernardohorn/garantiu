import streamlit as st

from garantiu.bug_history import build_bug_history
from garantiu.decision_log import get_decision_history, record_decision
from garantiu.git_reader import get_changed_files
from garantiu.incidents import load_incidents
from garantiu.manual_test_guide import build_module_card
from garantiu.scoring import score_modules, score_release
from garantiu.test_reports import parse_junit_report, test_health_by_module

st.set_page_config(page_title="garantiu", layout="wide")

if "analysis" not in st.session_state:
    st.session_state.analysis = None

screen = st.sidebar.radio(
    "Tela",
    ["Conectar Release", "Visão Geral do Risco", "Roteiro de Teste Manual", "Decisão de Publicação"],
)

if screen == "Conectar Release":
    st.title("Conectar release")
    repo_path = st.text_input("Caminho do repositório", value=".")
    base_ref = st.text_input("Comparar desde", value="HEAD~1")
    head_ref = st.text_input("Branch do release", value="HEAD")
    junit_path = st.text_input("Relatório de testes (JUnit XML)", value="sample_data/sample_junit.xml")
    incidents_path = st.text_input("Arquivo de incidentes (CSV)", value="sample_data/incidents.csv")

    if st.button("Analisar mudanças"):
        changed_files = get_changed_files(repo_path, base_ref, head_ref)
        bug_history = build_bug_history(repo_path)
        test_results = parse_junit_report(junit_path)
        test_health = test_health_by_module(test_results)
        incidents = load_incidents(incidents_path)

        # flakiness real entra na Task 9; até lá, roda sem esse sub-sinal.
        module_scores = score_modules(changed_files, bug_history, test_health, incidents, flakiness={})
        release = score_release(module_scores)

        st.session_state.analysis = {
            "release_name": head_ref,
            "changed_files": changed_files,
            "module_scores": module_scores,
            "release": release,
        }
        st.success(f"{len(changed_files)} arquivo(s) analisado(s) em {len(module_scores)} módulo(s).")

elif screen == "Visão Geral do Risco":
    st.title("Visão geral do risco")
    analysis = st.session_state.analysis
    if not analysis:
        st.info("Analise um release na tela 'Conectar Release' primeiro.")
    else:
        release = analysis["release"]
        st.metric("Score do release", f"{release['score']:.0f}/100")
        st.caption(f"Puxado pelo módulo: {release['top_module']}")

        st.subheader("Composição do score (módulo de maior risco)")
        for factor, value in release["factors"].items():
            st.progress(min(value, 100) / 100, text=f"{factor}: {value:.0f}")

        st.subheader("Módulos mais arriscados")
        st.table([
            {"Módulo": m["module"], "Score": m["score"]}
            for m in analysis["module_scores"]
        ])

elif screen == "Roteiro de Teste Manual":
    st.title("Roteiro de teste manual")
    analysis = st.session_state.analysis
    if not analysis:
        st.info("Analise um release na tela 'Conectar Release' primeiro.")
    else:
        for m in analysis["module_scores"]:
            card = build_module_card(m["module"], m["score"], m["factors"], analysis["changed_files"])
            with st.container(border=True):
                st.subheader(f"{card['module']} — risco {card['risk']}")
                st.write("**O que mudou**")
                st.write(card["o_que_mudou"])
                st.write("**Por que testar isso**")
                st.write(card["por_que_testar"])
                st.write("**Cenários sugeridos**")
                for cenario in card["cenarios"]:
                    st.write(f"- {cenario}")

elif screen == "Decisão de Publicação":
    st.title("Decisão de publicação")
    analysis = st.session_state.analysis
    if not analysis:
        st.info("Analise um release na tela 'Conectar Release' primeiro.")
    else:
        release = analysis["release"]
        st.metric("Score atual", f"{release['score']:.0f}/100")
        decided_by = st.text_input("Seu nome")

        col1, col2 = st.columns(2)
        if col1.button("Publicar mesmo assim") and decided_by:
            record_decision("garantiu.db", analysis["release_name"], release["score"], decided_by, "publicar")
            st.success("Decisão registrada: publicar.")
        if col2.button("Cancelar publicação") and decided_by:
            record_decision("garantiu.db", analysis["release_name"], release["score"], decided_by, "cancelar")
            st.warning("Decisão registrada: cancelar.")

        st.subheader("Registro (auditoria)")
        history = get_decision_history("garantiu.db", analysis["release_name"])
        st.table(history)
