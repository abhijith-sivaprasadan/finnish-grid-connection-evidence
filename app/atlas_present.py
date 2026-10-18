"""Editorial presentation of the Finnish evidence workbench.

Only layout and descriptive text live here. Verified observational metrics,
filters, links, plots and data exports remain native Streamlit components in
dashboard.py. No custom JS, embedded secrets or client-side API calls.
"""
from __future__ import annotations

from html import escape
from pathlib import Path


PALETTE = ("#20513d", "#b18843", "#9e4e35", "#316b50", "#607f86", "#6a695e")


def load_css() -> str:
    return Path(__file__).with_name("atlas_theme.css").read_text(encoding="utf-8")


def render_masthead(st) -> None:
    st.markdown("<style>" + load_css() + "</style>", unsafe_allow_html=True)
    st.markdown(
        """
<div class="fg-site-header">
  <a class="fg-brand" href="https://finnish-grid-atlas.streamlit.app/"
     aria-label="Finnish Grid Atlas home"><span class="fg-brand-mark">FG</span>
     <span>finnish<b>grid</b>atlas</span></a>
  <nav class="fg-nav" aria-label="Research links">
    <a href="#atlas-workbench">Explore evidence</a>
    <a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence"
       target="_blank" rel="noopener noreferrer">Methods &amp; code ↗</a>
    <a href="https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/"
       target="_blank" rel="noopener noreferrer">Operator source ↗</a>
  </nav>
</div>
<section class="fg-hero" aria-labelledby="fg-hero-title">
  <div>
    <p class="fg-eyebrow">Finland · grid connection evidence · public research dashboard</p>
    <h1 id="fg-hero-title">Where do public estimates show
      <em>potential to connect?</em></h1>
    <p class="fg-lede">An evidence-first view of indicative transmission-grid
      connection figures and Finland-wide electricity operations. Compare
      source-defined years and directions while keeping uncertainty, coverage
      gaps and data provenance visible.</p>
  </div>
  <aside class="fg-hero-panel">
    <span class="fg-small">Scope of the evidence</span>
    <strong>A published estimate is not an available connection.</strong>
    <p>Grid Scope observations are conditional and source-transcribed.
       National load and production are context—not measurements of local
       headroom. No individual connection has been confirmed or reserved.</p>
  </aside>
</section>
        """,
        unsafe_allow_html=True,
    )


def render_evidence_explainer(st) -> None:
    st.markdown(
        """
<div class="fg-evidence-row" aria-label="How to read the evidence">
  <article class="fg-card">
    <span class="fg-label">01 · Connection outlook</span>
    <h3>What was published?</h3>
    <p>Point-specific consumption and production estimates in discrete
       reported years, with no interpolation or aggregation.</p>
  </article>
  <article class="fg-card">
    <span class="fg-label">02 · System chronology</span>
    <h3>What was happening nationally?</h3>
    <p>Fingrid and ENTSO-E operational intervals, retaining their units,
       retrieval histories and original data-source identities.</p>
  </article>
  <article class="fg-card">
    <span class="fg-label">03 · Validation boundary</span>
    <h3>What is not proven?</h3>
    <p>Source transcription is not an independent numeric recheck.
       Grid connectability needs operator studies and formal process.</p>
  </article>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_section(st, eyebrow: str, title: str, description: str, *, anchor: str = "") -> None:
    anchor_attr = f' id="{escape(anchor, quote=True)}"' if anchor else ""
    st.markdown(
        f'<section class="fg-sectionhead"{anchor_attr}>'
        f'<p class="fg-eyebrow">{escape(eyebrow)}</p>'
        f'<h2>{escape(title)}</h2>'
        f'<p>{escape(description)}</p></section>',
        unsafe_allow_html=True,
    )


def render_footer(st) -> None:
    st.markdown(
        """
<footer class="fg-footer">
  <span>Finnish Grid Atlas · independent research prototype<br>
  Indicative evidence only · not a grid connection offer</span>
  <span>
    <a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence"
       target="_blank" rel="noopener noreferrer">Source code and methodology ↗</a>
    &nbsp; · &nbsp;
    <a href="https://kerala2040.github.io/"
       target="_blank" rel="noopener noreferrer">Design lineage: Kerala2040 ↗</a>
  </span>
</footer>
        """,
        unsafe_allow_html=True,
    )


def style_plot(fig, *, height=400, legend=True):
    """Paper-toned plot while retaining native source units and no interpolation."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#fffdf5", plot_bgcolor="#fffdf5",
        font={"family": "DM Sans, sans-serif", "color": "#143b30", "size": 12},
        title_font={"family": "Playfair Display, Georgia, serif"},
        height=height,
        margin={"t": 26, "l": 20, "r": 18, "b": 28},
        legend={"orientation": "h", "y": -0.24, "x": 0,
                "font": {"size": 11}},
        hoverlabel={"bgcolor": "#fffdf5", "font_color": "#143b30"},
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e6dfd0", linecolor="#bdb9aa",
                     zeroline=False, title_font={"size": 12})
    fig.update_yaxes(showgrid=True, gridcolor="#e6dfd0", linecolor="#bdb9aa",
                     zeroline=False, title_font={"size": 12})
    if not legend:
        fig.update_layout(showlegend=False)
    return fig
