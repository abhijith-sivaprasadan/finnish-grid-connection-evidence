"""Run with: python -m streamlit run app/dashboard.py"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import streamlit as st
from src.db import connect, db_path
from src.quality import report
from src.views import published, filter_capacity, coverage_matrix

st.set_page_config(page_title="Finnish Grid Evidence", page_icon="⚡", layout="wide")
st.caption("FINLAND  /  CONNECTION EVIDENCE")
st.title("Where capacity is published.")
st.markdown("Explore Fingrid's indicative connection estimates, with a traceable source for every observation.")
st.info("Personal portfolio proof of concept. Published estimates are not connection rights, reservations, or operator confirmation. Screening is not a validated grid planning study.")

with connect() as conn:
    capacity = published(conn)
    points = pd.read_sql_query("SELECT * FROM connection_point ORDER BY name", conn)
    context = pd.read_sql_query("SELECT * FROM latest_operational ORDER BY timestamp_utc", conn)
    projects = pd.read_sql_query("SELECT * FROM grid_project", conn)
    scenarios = pd.read_sql_query("SELECT * FROM scenario_result", conn)
    quality = report(conn)

a, b, c = st.columns(3)
a.metric("Connection points", len(points))
b.metric("Published observations", len(capacity))
c.metric("Operational records", len(context))
if context.empty:
    st.warning("Live operational context is pending API setup. Capacity observations below are real source transcriptions; no synthetic operational data is shown.")

estimate_tab, context_tab, project_tab, evidence_tab = st.tabs(
    ["Published estimates", "National context", "Planned projects", "Evidence & quality"])

with estimate_tab:
    if capacity.empty:
        st.info("No published observations loaded. Run python -m src.cli import-manual from the repo root.")
    else:
        with st.sidebar:
            st.header("Explore estimates")
            labels = dict(zip(points.connection_point_id, points.name))
            selected = st.multiselect("Connection points", list(labels), default=list(labels), format_func=labels.get)
            direction = st.selectbox("Direction", ["consumption", "production"])
            snapshot = st.selectbox("Source snapshot (UTC)", sorted(capacity.source_observed_at.unique(), reverse=True))
            source = st.selectbox("Source", sorted(capacity.source_url.unique()))
            years_available = sorted(int(x) for x in capacity.effective_year.dropna().unique())
            years = st.multiselect("Effective years", years_available, default=years_available)
            st.caption("Snapshot = capture time. Publication date stays blank unless the operator states it.")
            st.button("Reload database", help="Reruns the app to read the current database.")
        selected_frame = filter_capacity(capacity, selected, direction, years, snapshot, source)
        st.subheader(f"{direction.capitalize()} connection estimates")
        st.caption("Discrete published values only. Estimates at different points are not additive; connecting one project can affect others. No interpolation between years.")
        chart = selected_frame.dropna(subset=["capacity_value", "effective_year"])
        if chart.empty:
            st.info("Not published for the selected filters. This does not mean zero capacity.")
        else:
            # Separate plots prevent accidental comparison of MW with MVA.
            for unit, group in chart.groupby("capacity_unit"):
                fig = px.scatter(group, x="effective_year", y="capacity_value", color="name",
                    hover_data=["direction", "source_observed_at", "capacity_status", "validity_notes", "source_url"],
                    labels={"effective_year": "Published effective year", "capacity_value": f"Indicative capacity ({unit})", "name": "Point"},
                    color_discrete_sequence=["#087F8C", "#F49D37", "#6F5EAD", "#207A52", "#B54658"])
                fig.update_traces(marker={"size": 12, "line": {"width": 1, "color": "white"}})
                fig.update_xaxes(tickmode="array", tickvals=years, tickformat="d")
                fig.update_layout(height=400, margin={"t": 10, "l": 10, "r": 10, "b": 10}, legend={"orientation": "h", "y": -0.2})
                st.plotly_chart(fig, width="stretch")
        pairs = [(p, labels[p]) for p in selected]
        matrix = coverage_matrix(selected_frame, pairs, direction, years)
        if not matrix.empty:
            st.dataframe(matrix.pivot(index="Connection point", columns="Year", values="Published estimate"), width="stretch")
        st.caption('"not published" means absent from this compiled selection, not necessarily absent from the operator website.')
        with st.expander("Source records and caveats"):
            st.dataframe(selected_frame, hide_index=True, width="stretch",
                         column_config={"source_url": st.column_config.LinkColumn("Source")})
        st.download_button("Download selected evidence (CSV)", selected_frame.to_csv(index=False),
                           "published-estimates.csv", "text/csv")
        current = capacity[capacity.effective_year.isna()]
        if not current.empty:
            st.subheader("Current estimates without a published year")
            current = filter_capacity(current, selected, direction, snapshot=snapshot, source=source)
            st.dataframe(current, hide_index=True)

with context_tab:
    st.subheader("Finland-wide operational context")
    st.write("These are national or bidding-zone time series. They are not measurements at the selected substations and are not estimates of connection capacity.")
    if context.empty:
        st.info("Configure FINGRID_API_KEY and ENTSOE_API_TOKEN, then run the ingestion commands in docs/SETUP.md.")
        st.code("python -m src.cli fingrid --start 2026-10-15T00:00:00Z --end 2026-10-16T00:00:00Z")
    else:
        series_options = context[["source", "dataset_id", "metric", "unit"]].drop_duplicates()
        choices = list(series_options.itertuples(index=False, name=None))
        chosen = st.selectbox("Operational series", choices, format_func=lambda x: " / ".join(x))
        frame = context.copy()
        for field, value in zip(["source", "dataset_id", "metric", "unit"], chosen):
            frame = frame[frame[field] == value]
        st.caption(f"Latest retrieval: {frame.retrieved_at.max()} · UTC intervals · latest retrieved revision per interval")
        st.plotly_chart(px.scatter(frame, x="timestamp_utc", y="value", labels={"value": chosen[3]},
                                  hover_data=["interval_end_utc", "source_url"]), width="stretch")
        st.dataframe(frame, hide_index=True)

with project_tab:
    st.subheader("Planned reinforcements")
    st.write("A planned commissioning date is uncertain and does not establish a guaranteed MW release.")
    if projects.empty:
        st.info("No project-to-substation relationships have been source-verified in this release.")
    else:
        st.dataframe(projects, hide_index=True)

with evidence_tab:
    st.subheader("Evidence categories")
    st.dataframe(pd.DataFrame([
        ["Published indicative", "Operator-published estimate", "Default capacity view"],
        ["Operational context", "National load and generation time series", "Separate context tab"],
        ["Model scenario", "Assumption-dependent study output", "Separate scenario storage; stretch"],
        ["Operator confirmed", "Requires documentary confirmation", "Not present in this public sample"],
    ], columns=["Category", "Meaning", "Presentation"]), hide_index=True)
    st.subheader("Quality and readiness")
    for issue in quality["issues"]:
        st.warning(issue)
    st.json(quality["counts"])
    st.caption(f"SQLite: {db_path()}")
    st.markdown("[Grid Scope](https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/) · "
                "[Fingrid Open Data](https://data.fingrid.fi/en/instructions) · "
                "[ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)")
    st.write("Source capture and spot checks verify transcription. They do not validate the operator's estimates against network studies. See docs/SOURCES.md for the capture method and reuse terms.")
    with st.expander("Model-derived scenarios (optional stretch)"):
        if scenarios.empty:
            st.info("No model runs have been performed. PyPSA and pandapower are outside this release.")
        else:
            st.warning("Assumption-dependent model output; never a published connection estimate.")
            st.dataframe(scenarios, hide_index=True)
