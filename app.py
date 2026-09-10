"""Local release risk dashboard. Run with python -m streamlit run app.py."""

import os
import sqlite3
from pathlib import Path

import git
import streamlit as st
from junitparser import JUnitXmlError

from garantiu.bug_history import bug_history_detail_by_module, build_bug_history
from garantiu.decision_log import get_decision_history, record_decision
from garantiu.git_reader import (
    get_changed_files, is_documentation_change, resolve_comparison_base,
)
from garantiu.incidents import load_incident_details, load_incidents
from garantiu.manual_test_guide import build_module_card
from garantiu.module_detail import build_module_detail
from garantiu.release_history import (
    get_release_history, record_release_outcome, record_release_score,
)
from garantiu.scoring import score_modules, score_release
from garantiu.repository_source import prepare_repository, repository_key
from garantiu.test_history import flakiness_by_module, record_test_run
from garantiu.test_prioritization import prioritize_tests
from garantiu.test_reports import load_project_test_report, test_health_by_module
from garantiu.ui import (
    inject_design_system, render_brand, render_factor_heading,
    render_module_focus, render_page_header, render_release_context,
    render_risk_distribution, render_section_label, render_sidebar_footer,
    risk_level,
)

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("GARANTIU_DATA_DIR", ROOT))
DECISIONS_DB = str(DATA_DIR / "garantiu.db")
TEST_HISTORY_DB = str(DATA_DIR / "garantiu_test_history.db")
RELEASE_HISTORY_DB = str(DATA_DIR / "garantiu_release_history.db")
SCREENS = [
    "Conectar Release", "Visão Geral do Risco", "Roteiro de Teste Manual",
    "Suíte Automatizada Priorizada", "Detalhe do Módulo",
    "Decisão de Publicação", "Histórico & Tendências",
]


def connect_release():
    render_page_header(
        "01 · PREPARAR RELEASE", "Conectar release",
        "Escolha o código e o intervalo que serão avaliados antes de calcular o risco.",
    )
    render_section_label(
        "Origem da análise",
        "O Garantiu lê o histórico e as mudanças sem executar o código do repositório.",
    )
    repo_input = st.text_input(
        "Pasta local ou link do GitHub", value=".", key="repo_path",
        help="Ex.: C:\\Projetos\\meu-sistema ou https://github.com/usuario/projeto",
        on_change=lambda: st.session_state.update(analysis=None),
    )
    base_ref = st.text_input(
        "Comparar desde", value="AUTO",
        help="AUTO usa a última tag anterior à branch escolhida. Sem tags, "
             "usa o primeiro commit alcançável.",
    )
    head_ref = st.text_input("Branch do release", value="HEAD")
    with st.expander("Dados adicionais de qualidade (opcional)"):
        st.caption(
            "Enriqueça a análise com resultados reais de testes e incidentes. "
            "Sem essas fontes, o score usa somente as evidências disponíveis."
        )
        junit_path = st.text_input(
            "Relatório de testes (JUnit XML)",
            value="", key=f"junit_path:{repo_input}",
            help="Informe um arquivo local ou repo:reports/junit.xml para ler "
                 "um XML do commit selecionado. Deixe vazio se não houver relatório.",
        )
        incidents_path = st.text_input(
            "Arquivo de incidentes (CSV)",
            value="", key=f"incidents_path:{repo_input}",
        )
        incident_details_path = st.text_input(
            "Arquivo de detalhe de incidentes (CSV, opcional)",
            value="", key=f"incident_details_path:{repo_input}",
        )
    st.caption(
        "Links GitHub são lidos novamente em cada análise. JUnit pode ser local "
        "ou usar repo:caminho/arquivo.xml; os arquivos CSV permanecem locais."
    )
    if not st.button("Analisar mudanças", type="primary", use_container_width=True):
        return
    st.session_state.analysis = None
    with st.spinner("Lendo mudanças, testes e histórico..."):
        repo_path = st.session_state.repo_path.strip()
        if not repo_path or not base_ref.strip() or not head_ref.strip():
            raise ValueError("Informe o repositório e as duas referências Git.")
        with prepare_repository(repo_path) as source:
            repo_key = source.key
            with git.Repo(source.path) as repo:
                head_sha = repo.commit(head_ref.strip()).hexsha
                base_sha, base_label = resolve_comparison_base(
                    repo, base_ref, head_ref.strip(),
                )
                test_results = load_project_test_report(
                    repo, head_sha, junit_path,
                )
            all_changed_files = get_changed_files(
                source.path, base_sha, head_sha,
            )
            documentation_files = [
                change for change in all_changed_files
                if is_documentation_change(change["path"])
            ]
            changed_files = [
                change for change in all_changed_files
                if not is_documentation_change(change["path"])
            ]
            bug_history = build_bug_history(source.path, ref=head_sha)
            bug_details = {
                module: bug_history_detail_by_module(
                    source.path, module, ref=head_sha,
                )
                for module in {f["module"] for f in changed_files}
            }
        test_health = test_health_by_module(test_results)
        incidents = load_incidents(incidents_path.strip()) if incidents_path.strip() else {}
        incident_details = (
            load_incident_details(incident_details_path.strip())
            if incident_details_path.strip() else {}
        )
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if test_results:
            record_test_run(TEST_HISTORY_DB, test_results, repo_key=repo_key)
        flakiness = (
            flakiness_by_module(TEST_HISTORY_DB, repo_key=repo_key)
            if test_results else {}
        )
        module_scores = score_modules(
            changed_files, bug_history, test_health, incidents, flakiness,
        )
        release = score_release(module_scores)
        release_name = f"{head_ref.strip()} @ {base_label}..{head_sha[:8]}"
        record_release_score(
            RELEASE_HISTORY_DB, release_name, release["score"],
            repo_key=repo_key,
        )
        st.session_state.analysis = {
            "release_name": release_name, "repo_path": repo_key,
            "comparison_base": base_label,
            "all_changed_files": all_changed_files,
            "documentation_files": documentation_files,
            "changed_files": changed_files, "module_scores": module_scores,
            "release": release, "test_results": test_results,
            "junit_source": junit_path.strip(),
            "test_health": test_health, "flakiness": flakiness,
            "bug_details": bug_details, "incident_details": incident_details,
        }
        st.session_state.history_repo = repo_key
    st.success(
        f"{len(changed_files)} arquivo(s) de produto analisado(s) "
        f"em {len(module_scores)} módulo(s), dentro de "
        f"{len(all_changed_files)} alteração(ões) no intervalo."
    )
    if documentation_files:
        st.info(
            f"{len(documentation_files)} arquivo(s) apenas de documentação "
            "foram identificados e não influenciaram o score de risco."
        )
    if not changed_files:
        st.warning(
            "O intervalo não contém mudanças de produto para analisar. "
            "Escolha outra referência base se esperava alterações de código "
            "ou configuração."
        )


def risk_overview(analysis):
    render_page_header(
        "02 · AVALIAR RELEASE", "Visão geral do risco",
        "Entenda o impacto, encontre o foco do teste e avance com evidências.",
    )
    render_release_context(analysis)
    release = analysis["release"]
    if not analysis["module_scores"]:
        st.metric("Score de risco da release", f"{release['score']:.0f}/100")
        st.info("Nenhum módulo alterado neste intervalo.")
        return
    with st.container(border=True):
        score_col, distribution_col = st.columns([1.15, 1])
        with score_col:
            st.metric("Score de risco da release", f"{release['score']:.0f}/100")
            level, label = risk_level(release["score"])
            st.markdown(
                f"<strong class='risk-pill risk-{level}'>{label}</strong>",
                unsafe_allow_html=True,
            )
            st.caption(
                f"O módulo {release['top_module']} concentra o maior risco desta release."
            )
        with distribution_col:
            render_risk_distribution(analysis["module_scores"])
    risco = release["modulos_em_risco"]
    outros = risco["alto"] + risco["medio"] - 1
    if outros > 0:
        st.caption(
            f"O score do release é o do módulo mais arriscado, mas há mais "
            f"{outros} módulo(s) em risco alto/médio nesta mudança "
            f"({risco['alto']} em risco alto, {risco['medio']} em risco médio)."
        )
    render_section_label(
        f"Por que {release['top_module']} está em risco?",
        "Quatro sinais objetivos compõem o score do módulo mais crítico.",
    )
    factor_columns = st.columns(2)
    for index, (factor, value) in enumerate(release["factors"].items()):
        with factor_columns[index % 2]:
            render_factor_heading(factor, value)
            st.progress(min(value, 100) / 100)
    render_section_label(
        "Módulos por nível de risco",
        "Ordenados por risco e impacto para indicar onde testar primeiro.",
    )
    table_col, focus_col = st.columns([1.7, 1])
    with table_col:
        st.table([
            {"Módulo": m["module"], "Score": m["score"],
             "Nível": risk_level(m["score"])[1]}
            for m in analysis["module_scores"]
        ])
    with focus_col:
        render_module_focus(analysis["module_scores"][0])
        st.button(
            "Preparar teste manual", type="primary", use_container_width=True,
            on_click=lambda: st.session_state.update(screen=SCREENS[2]),
        )
    if any(m["module"] not in analysis["test_health"]
           for m in analysis["module_scores"]):
        st.info(
            "Há módulos sem testes correspondentes no relatório. A ausência "
            "de dados não aumenta o score, mas não comprova que estão testados."
        )


def manual_guide(analysis):
    render_page_header(
        "03 · DIRECIONAR TESTE", "Roteiro de teste manual",
        "Transforme evidências técnicas em cenários claros para quem vai testar.",
    )
    render_release_context(analysis)
    if not analysis["module_scores"]:
        st.info("Nenhum módulo alterado para gerar um roteiro.")
    for module in analysis["module_scores"]:
        card = build_module_card(
            module["module"], module["score"], module["factors"],
            analysis["changed_files"],
        )
        with st.container(border=True):
            st.subheader(f"{card['module']} — risco {card['risk']}")
            st.write("**O que mudou**")
            st.write(card["o_que_mudou"])
            st.write("**Por que testar isso**")
            st.write(card["por_que_testar"])
            st.write("**Cenários sugeridos**")
            for scenario in card["cenarios"]:
                st.write(f"- {scenario}")
            st.text_area(
                "Nota do dev pro QA (opcional)",
                key=f"nota_dev_{module['module']}",
                placeholder="Ex.: mexi na validação de cupom, atenção ao fluxo de desconto.",
            )


def automated_suite(analysis):
    render_page_header(
        "04 · PRIORIZAR AUTOMAÇÃO", "Suíte automatizada priorizada",
        "Consulte os testes importados na ordem que mais reduz o risco da release.",
    )
    render_release_context(analysis)
    st.caption(f"Repositório analisado: {analysis['repo_path']}")
    st.caption(f"Release: {analysis['release_name']}")
    if not analysis.get("junit_source"):
        st.info(
            "Nenhum relatório de testes foi fornecido para este projeto. "
            "Em Conectar Release, informe um JUnit local ou "
            "repo:reports/junit.xml e clique em Analisar mudanças."
        )
        st.caption(
            "Gere o relatório no seu terminal ou CI. Para projetos com pytest: "
            "python -m pytest --junitxml=relatorio.xml. "
            "O Garantiu não executa automaticamente o código do repositório."
        )
        return
    st.caption(f"Relatório utilizado: {analysis['junit_source']}")
    ordered = prioritize_tests(
        analysis["test_results"], analysis["module_scores"],
        analysis["flakiness"],
    )
    st.caption(
        "Ordem recomendada a partir do relatório importado. "
        "A execução dos testes acontece no seu terminal ou CI."
    )
    if not ordered:
        st.info("O relatório não contém testes.")
        return
    changed_modules = {m["module"] for m in analysis["module_scores"]}
    unmatched = sorted({t["module"] for t in ordered} - changed_modules)
    if unmatched:
        st.warning(
            "Há testes sem associação aos módulos alterados: "
            + ", ".join(unmatched)
            + ". Podem ser de áreas não alteradas ou usar nomes diferentes. "
            "Eles não recebem prioridade por risco. Confira o relatório "
            "e a correspondência entre classname e as pastas do projeto."
        )
    st.table([
        {"Teste": t["name"], "Módulo": t["module"], "Status": t["status"],
         "Tempo (s)": t["time"], "Flakiness do módulo (%)": t["flakiness"],
         "Score do módulo": (t["module_score"]
                             if t["module"] in changed_modules else None)}
        for t in ordered
    ])


def module_detail(analysis):
    render_page_header(
        "05 · EXPLICAR RISCO", "Detalhe do módulo",
        "Veja as evidências que sustentam o risco de cada área alterada.",
    )
    render_release_context(analysis)
    modules = [m["module"] for m in analysis["module_scores"]]
    if not modules:
        st.info("Nenhum módulo alterado para detalhar.")
        return
    selected = st.selectbox("Módulo", modules)
    detail = build_module_detail(
        selected, analysis["changed_files"],
        analysis["bug_details"].get(selected, []),
        analysis["incident_details"].get(selected, []),
        analysis["test_health"], analysis["flakiness"],
    )
    st.subheader("O que mudou")
    st.table([
        {"Arquivo": f["path"], "+": f["lines_added"], "-": f["lines_removed"]}
        for f in detail["files"]
    ])
    st.subheader("Histórico de bugs")
    if detail["bugs"]:
        st.table(detail["bugs"])
    else:
        st.caption("Nenhum bug histórico registrado para esse módulo.")
    st.subheader("Incidentes em produção")
    if detail["incidents"]:
        st.table(detail["incidents"])
    else:
        st.caption("Nenhum detalhe de incidente informado para esse módulo.")
    st.subheader("Saúde dos testes")
    if selected in analysis["test_health"]:
        st.write(
            f"Taxa de aprovação na última rodada: {detail['test_health']:.0f}%"
        )
    else:
        st.info("Sem testes correspondentes no relatório atual.")
    st.write(f"Flakiness histórica: {detail['flakiness']:.0f}%")


def publication_decision(analysis):
    render_page_header(
        "06 · DECIDIR", "Decisão de publicação",
        "Registre uma decisão humana consciente; o Garantiu não executa o deploy.",
    )
    render_release_context(analysis)
    release = analysis["release"]
    with st.container(border=True):
        score_col, decision_col = st.columns([.8, 1.6])
        with score_col:
            st.metric("Score atual", f"{release['score']:.0f}/100")
            level, label = risk_level(release["score"])
            st.markdown(
                f"<strong class='risk-pill risk-{level}'>{label}</strong>",
                unsafe_allow_html=True,
            )
        with decision_col:
            st.subheader("Responsável pela decisão")
            st.caption(
                "Seu nome identifica o registro de auditoria. Isto não substitui autenticação."
            )
            decided_by = st.text_input("Seu nome").strip()
            decision_key = f"{analysis['repo_path']} :: {analysis['release_name']}"
            col1, col2 = st.columns(2)
            publish = col1.button(
                "Publicar mesmo assim", disabled=not decided_by,
                type="primary", use_container_width=True,
            )
            cancel = col2.button(
                "Cancelar publicação", disabled=not decided_by,
                use_container_width=True,
            )
    if publish or cancel:
        decision = "publicar" if publish else "cancelar"
        record_decision(
            DECISIONS_DB, decision_key, release["score"], decided_by, decision,
        )
        st.success(f"Decisão registrada: {decision}.")
    render_section_label(
        "Registro de auditoria",
        "Decisões anteriores desta mesma release, em ordem cronológica.",
    )
    history = get_decision_history(DECISIONS_DB, decision_key)
    if history:
        st.table(history)
    else:
        st.info("Nenhuma decisão registrada para este release.")


def release_trends():
    render_page_header(
        "07 · APRENDER", "Histórico & tendências",
        "Compare risco previsto e resultado real para construir confiança no score.",
    )
    repo_path = st.text_input(
        "Repositório do histórico (pasta ou link do GitHub)",
        value=st.session_state.get("history_repo", str(ROOT)),
    )
    repo_key = repository_key(repo_path)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = get_release_history(RELEASE_HISTORY_DB, repo_key=repo_key)
    if not history:
        st.info("Ainda não há releases analisados para este repositório.")
        return
    st.table(history)
    st.subheader("Evolução do score previsto")
    st.line_chart([
        {"Analisado em (UTC)": h["computed_at"], "Score": h["score"]}
        for h in reversed(history)
    ], x="Analisado em (UTC)", y="Score")
    st.caption(
        "Compare os scores com os resultados reais na tabela. "
        "O score é um indicador relativo, não uma probabilidade de falha."
    )
    st.subheader("Marcar resultado real de um release")
    release_to_mark = st.selectbox("Release", [h["release"] for h in history])
    outcome = st.radio(
        "Resultado", ["ok", "falhou"], horizontal=True, key="outcome",
    )
    if st.button("Registrar resultado"):
        record_release_outcome(
            RELEASE_HISTORY_DB, release_to_mark, outcome, repo_key=repo_key,
        )
        st.rerun()


st.set_page_config(page_title="garantiu", page_icon="G", layout="wide")
inject_design_system()
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "screen" not in st.session_state:
    st.session_state.screen = SCREENS[0]
render_brand()
screen = st.sidebar.radio("Fluxo da release", SCREENS, key="screen")
render_sidebar_footer()
try:
    if screen == SCREENS[0]:
        connect_release()
    elif screen == SCREENS[6]:
        release_trends()
    elif not st.session_state.analysis:
        render_page_header(
            "FLUXO DA RELEASE", screen,
            "Conecte e analise uma release para liberar esta etapa.",
        )
        st.info("Analise um release na tela 'Conectar Release' primeiro.")
    else:
        renderers = {
            SCREENS[1]: risk_overview, SCREENS[2]: manual_guide,
            SCREENS[3]: automated_suite, SCREENS[4]: module_detail,
            SCREENS[5]: publication_decision,
        }
        renderers[screen](st.session_state.analysis)
except (OSError, ValueError, git.GitError, git.BadName,
        git.BadObject, JUnitXmlError) as exc:
    st.error(f"Não foi possível concluir a operação. Confira os dados: {exc}")
except sqlite3.Error:
    st.error(
        "Não foi possível acessar ou gravar o histórico local. "
        "Confira a permissão da pasta de dados e tente novamente."
    )
