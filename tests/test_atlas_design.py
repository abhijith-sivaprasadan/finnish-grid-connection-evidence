"""Editorial presentation checks (no browser or external font dependency)."""
from pathlib import Path

import plotly.express as px
from app.atlas_present import (
    load_css, render_masthead, render_evidence_explainer,
    render_section, render_footer, style_plot, PALETTE,
)
from src.db import ROOT


class CollectMarkdown:
    def __init__(self):
        self.blocks=[]
    def markdown(self, value, **kwargs):
        assert kwargs.get("unsafe_allow_html") is True
        self.blocks.append(value)


def test_theme_reflects_research_site_paper_and_forest_palette():
    css=load_css()
    assert "--fg-paper:#f7f2e4" in css
    assert "--fg-leaf:#20513d" in css
    assert "--fg-rust:#9e4e35" in css
    assert "Playfair Display" in css
    assert "DM Mono" in css
    assert "@media(max-width:620px)" in css
    assert "prefers-reduced-motion" in css
    config=(ROOT / ".streamlit/config.toml").read_text(encoding="utf-8")
    assert 'base = "light"' in config
    assert '#F7F2E4' in config


def test_masthead_research_links_and_caveat_are_source_safe():
    sink=CollectMarkdown()
    render_masthead(sink)
    render_evidence_explainer(sink)
    render_footer(sink)
    all_markup="\n".join(sink.blocks)
    assert 'class="fg-hero"' in all_markup
    assert 'class="fg-site-header"' in all_markup
    assert 'class="fg-evidence-row"' in all_markup
    assert "finnish-grid-atlas.streamlit.app" in all_markup
    assert "kerala2040.github.io" in all_markup
    assert "not an available connection" in all_markup
    assert "No individual connection has been confirmed" in all_markup
    assert "<script" not in all_markup.lower()


def test_section_escapes_injected_titles():
    sink=CollectMarkdown()
    render_section(sink, "safe", "<script>alert(1)</script>", "Text & data",
                   anchor="atlas-workbench")
    content=sink.blocks[0]
    assert "&lt;script&gt;" in content
    assert "<script>" not in content
    assert "Text &amp; data" in content
    assert 'id="atlas-workbench"' in content


def test_plotly_uses_editorial_colors_without_inventing_series():
    fig=px.scatter(x=["2026", "2030"],y=[100, 200])
    before=len(fig.data)
    result=style_plot(fig, legend=False)
    assert result is fig
    assert len(fig.data)==before
    assert result.layout.paper_bgcolor=="#fffdf5"
    assert result.layout.plot_bgcolor=="#fffdf5"
    assert result.layout.showlegend is False
    assert PALETTE[0]=="#20513d"


def test_dashboard_imports_presentation_without_removed_evidence_controls():
    code=(ROOT / "app/dashboard.py").read_text(encoding="utf-8")
    for feature in ("render_masthead(st)", "render_evidence_explainer(st)",
                    "render_footer(st)", "comparison_grid(", "audit_rows(",
                    "filter_capacity(", "st.download_button(",
                    "source_observed_at", "evidence_tab"):
        assert feature in code
