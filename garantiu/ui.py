"""Presentation helpers for the Garantiu Streamlit interface."""

from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
BRAND_ASSET_DIR = ROOT / "garantiu" / "assets"
BRAND_FULL_PATH = BRAND_ASSET_DIR / "garantiu-logo-full.jpeg"
BRAND_SYMBOL_PATH = BRAND_ASSET_DIR / "garantiu-symbol.png"
BRAND_WORDMARK_PATH = BRAND_ASSET_DIR / "garantiu-wordmark.png"
FACTOR_LABELS = {
    "complexidade": "Complexidade da mudança",
    "bugs": "Histórico de bugs",
    "saude_testes": "Saúde dos testes",
    "incidentes": "Incidentes anteriores",
}


@lru_cache(maxsize=3)
def _asset_data_uri(path: Path) -> str:
    """Embed a local brand asset without depending on a static file server."""
    mime_type = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{payload}"


def inject_design_system() -> None:
    """Load the shared visual system once per Streamlit render."""
    css = (ROOT / "garantiu" / "ui.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_brand() -> None:
    """Render the product signature and promise in the sidebar."""
    full_logo = _asset_data_uri(BRAND_FULL_PATH)
    st.sidebar.markdown(
        f"""
        <div class="brand-lockup">
          <div class="brand-full-crop">
            <img src="{full_logo}" alt="Garantiu" />
          </div>
          <p>Da evidência para entregas com segurança.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer() -> None:
    wordmark = _asset_data_uri(BRAND_WORDMARK_PATH)
    st.sidebar.markdown(
        f"""
        <div class="sidebar-footer">
          <img src="{wordmark}" alt="Garantiu" />
          <span>Engenharia de software<br>com mais confiança.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(eyebrow: str, title: str, description: str) -> None:
    symbol = _asset_data_uri(BRAND_SYMBOL_PATH)
    st.markdown(
        f"""
        <div class="page-brand-symbol" aria-hidden="true">
          <img src="{symbol}" alt="" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p class='page-eyebrow'>{escape(eyebrow)}</p>",
        unsafe_allow_html=True,
    )
    st.title(title)
    st.markdown(
        f"<p class='page-description'>{escape(description)}</p>",
        unsafe_allow_html=True,
    )


def render_release_context(analysis: dict) -> None:
    """Keep the analyzed source visible without inventing unavailable data."""
    release_name = escape(str(analysis.get("release_name", "Release atual")))
    repo_path = escape(str(analysis.get("repo_path", "Repositório não informado")))
    changed = len(analysis.get("changed_files", []))
    modules = len(analysis.get("module_scores", []))
    st.markdown(
        f"""
        <section class="release-context" aria-label="Contexto da release">
          <div>
            <span class="context-label">RELEASE ANALISADA</span>
            <strong>{release_name}</strong>
            <small>{repo_path}</small>
          </div>
          <dl>
            <div><dt>ARQUIVOS</dt><dd>{changed}</dd></div>
            <div><dt>MÓDULOS</dt><dd>{modules}</dd></div>
            <div><dt>STATUS</dt><dd><span class="status-dot">Analisada</span></dd></div>
          </dl>
        </section>
        """,
        unsafe_allow_html=True,
    )


def risk_level(score: float) -> tuple[str, str]:
    if score >= 70:
        return "alto", "Alto risco"
    if score >= 40:
        return "medio", "Médio risco"
    return "baixo", "Baixo risco"


def render_risk_distribution(module_scores: list[dict]) -> None:
    counts = {"alto": 0, "medio": 0, "baixo": 0}
    for module in module_scores:
        counts[risk_level(float(module["score"]))[0]] += 1
    st.markdown(
        f"""
        <div class="risk-distribution" aria-label="Distribuição dos módulos por risco">
          <div><strong>{len(module_scores)}</strong><span>módulos impactados</span></div>
          <div class="risk-high"><strong>{counts['alto']}</strong><span>em alto risco</span></div>
          <div class="risk-medium"><strong>{counts['medio']}</strong><span>em médio risco</span></div>
          <div class="risk-low"><strong>{counts['baixo']}</strong><span>em baixo risco</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_factor_heading(factor: str, value: float) -> None:
    label = FACTOR_LABELS.get(factor, factor.replace("_", " ").title())
    level, level_label = risk_level(value)
    st.markdown(
        f"""
        <div class="factor-heading">
          <span>{escape(label)}</span>
          <strong class="risk-{level}">{value:.0f}<small>/100 · {level_label}</small></strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_label(title: str, description: str | None = None) -> None:
    detail = f"<span>{escape(description)}</span>" if description else ""
    st.markdown(
        f"<div class='section-label'><strong>{escape(title)}</strong>{detail}</div>",
        unsafe_allow_html=True,
    )


def render_module_focus(module: dict) -> None:
    level, label = risk_level(float(module["score"]))
    st.markdown(
        f"""
        <div class="module-focus">
          <span>FOCO RECOMENDADO</span>
          <h3>{escape(str(module['module']))}</h3>
          <p>Este módulo concentra o maior risco desta release. Comece por ele e use as evidências abaixo para orientar o teste.</p>
          <strong class="risk-pill risk-{level}">{label} · {float(module['score']):.0f}/100</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
