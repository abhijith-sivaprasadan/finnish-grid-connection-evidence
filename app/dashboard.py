"""Run with: python -m streamlit run app/dashboard.py"""
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import streamlit as st
from src.db import connect, db_path
from src.quality import report
from src.views import published, filter_capacity, coverage_matrix
from src.availability import comparison_grid, coverage_summary
from src.audit_capacity import audit_rows
from src.cloud_store import engine_for, read_snapshot
from app.atlas_present import (
    PALETTE, render_masthead, render_evidence_explainer,
    render_section, render_footer, style_plot,
)

st.set_page_config(page_title="Finnish Grid Atlas · Connection Evidence", page_icon="⚡", layout="wide")
render_masthead(st)

# Hosted deployment must be explicitly enabled; otherwise keep the existing
# local SQLite behavior. Public visitors NEVER receive database/API credentials.
hosted = os.environ.get("HOSTED_DASHBOARD", "").lower() == "true"
if hosted:
    read_url = os.environ.get("DATABASE_READ_URL", "")
    if not read_url:
        st.error("Hosted database is not configured. No live data is being presented.")
        st.stop()

    @st.cache_data(ttl=600, show_spinner=False)
    def load_hosted(_url):
        engine = engine_for(_url)
        try:
            return read_snapshot(engine)
        finally:
            engine.dispose()

    try:
        snapshot_data = load_hosted(read_url)
    except Exception:
        # SQL driver exceptions may include credentials: never display them.
        st.error("Hosted evidence database temporarily unavailable. No source values were invented.")
        st.stop()
    capacity = snapshot_data["capacity"]
    points = snapshot_data["points"]
    context = snapshot_data["context"]
    projects = snapshot_data["projects"]
    scenarios = snapshot_data["scenarios"]
    quality = snapshot_data["quality"]
    audit_checklist = []
    for r in capacity.itertuples(index=False):
        audit_checklist.append({
            "observation_id": r.observation_id,
            "connection_point": r.name,
            "direction": r.direction,
            "effective_year": r.effective_year,
            "recorded_value": r.capacity_value,
            "recorded_unit": r.capacity_unit,
            "source_url": r.source_url,
            "source_observed_at": r.source_observed_at,
            "source_published_on": r.source_published_on or "",
            "capacity_status": r.capacity_status,
            "validity_notes": r.validity_notes,
            "independent_recheck_status": "pending_independent_recheck",
            "rechecked_on_utc": "",
            "verified_value": "",
            "verified_unit": "",
            "verification_evidence_url": "",
            "review_notes": "",
        })
    st.caption("Hosted read-only PostgreSQL snapshot · source ingestion is scheduled separately")
else:
    with connect() as conn:
        capacity = published(conn)
        points = pd.read_sql_query("SELECT * FROM connection_point ORDER BY name", conn)
        context = pd.read_sql_query("SELECT * FROM latest_operational ORDER BY timestamp_utc", conn)
        projects = pd.read_sql_query("SELECT * FROM grid_project", conn)
        scenarios = pd.read_sql_query("SELECT * FROM scenario_result", conn)
        quality = report(conn)
        audit_checklist = audit_rows(conn)

render_section(
    st, "Current evidence base", "A transparent starting point, not a connection offer.",
    "These counters describe what's stored in this evidence collection. Published "
    "The 18 ORIGINAL indicative Grid Scope transcription values were screenshot-matched on 18–19 October 2026; physical capacity and connection rights remain unverified.",
)
a, b, c = st.columns(3)
a.metric("Connection points", len(points))
b.metric("Published observations", len(capacity))
c.metric("Operational records", len(context))
if context.empty:
    st.warning("No persisted operational rows available for this selected database. Prior authenticated smoke checks used temporary databases, not the hosted dataset. The original source values matched reviewer-provided screenshots; that is not a physical grid capacity validation.")
else:
    latest_record = pd.to_datetime(context["interval_end_utc"], utc=True).max()
    lag = (pd.Timestamp.now(tz="UTC") - latest_record).total_seconds() / 3600
    st.caption(f"Newest displayed national operational interval: {latest_record.strftime('%Y-%m-%d %H:%M UTC')} · {lag:.0f} hours behind current UTC time")
    if lag > 120:
        st.warning("National operational data is older than five days. It must not be presented as live current measurements.")

render_evidence_explainer(st)
render_section(
    st, "Explore the evidence", "Follow the source, then the uncertainty.",
    "Filter the recorded capacity estimates, compare their published years, "
    "and inspect national operating conditions without conflating the datasets.",
    anchor="atlas-workbench",
)
estimate_tab, comparison_tab, context_tab, project_tab, evidence_tab = st.tabs(
    ["Published estimates", "Power availability outlook", "National context", "Planned projects", "Evidence & quality"])

with estimate_tab:
    render_section(st, "Grid Scope · observations",
                   "Point-by-point published estimates.",
                   "Source-defined connection directions and publication years. "
                   "Every numeric marker corresponds to a recorded estimate, "
                   "not a continuous availability forecast.")
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
        st.markdown(f"### {direction.capitalize()} connection estimates")
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
                    color_discrete_sequence=PALETTE)
                fig.update_traces(marker={"size": 12, "line": {"width": 1, "color": "white"}})
                fig.update_xaxes(tickmode="array", tickvals=years, tickformat="d")
                st.plotly_chart(style_plot(fig, height=420), width="stretch")
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

with comparison_tab:
    render_section(
        st, "Comparison · conditionally published years",
        "Capacity evidence in discrete time.",
        "Compare Fingrid Grid Scope's source-transcribed estimates by point, "
        "connection direction and published year. Each marker is a discrete "
        "source observation, not a forecast or confirmed offer.",
    )
    st.caption("Only one capture session is compared at a time. Missing entries are not zero MW, and points must not be summed. Forecast years are conditional.")
    if capacity.empty or points.empty:
        st.info("No published capacity source observations available. Run the manual source importer first.")
    else:
        all_years = sorted(int(year) for year in capacity.effective_year.dropna().unique())
        snapshots = sorted(capacity.source_observed_at.unique(), reverse=True)
        comp1, comp2 = st.columns(2)
        with comp1:
            outlook_snapshot = st.selectbox("Source capture session (UTC)", snapshots, key="outlook_snapshot")
            outlook_years = st.multiselect("Published years", all_years, default=all_years, key="outlook_years")
        with comp2:
            outlook_labels = dict(zip(points.connection_point_id, points.name))
            outlook_points = st.multiselect("Substations", list(outlook_labels),
                                            default=list(outlook_labels),
                                            format_func=outlook_labels.get, key="outlook_points")
        comparison_points = points[points.connection_point_id.isin(outlook_points)]
        outlook = comparison_grid(capacity, comparison_points, outlook_years,
                                  snapshot=outlook_snapshot)
        coverage = coverage_summary(outlook)
        n1, n2, n3 = st.columns(3)
        n1.metric("Published intersections", coverage["published"])
        n2.metric("Not published in selection", coverage["not_published_in_selection"])
        n3.metric("Needs source reconciliation", coverage["needs_reconciliation"])
        if not outlook.empty:
            for outlook_direction in ("consumption", "production"):
                st.markdown(f"#### {outlook_direction.capitalize()} · published indicative")
                direction_rows = outlook[outlook["Direction"] == outlook_direction]
                pivot = direction_rows.pivot(index="Connection point",
                                             columns="Year", values="Published estimate")
                st.dataframe(pivot, width="stretch")
                published_rows = direction_rows[direction_rows["Evidence"] == "published_indicative"]
                if published_rows.empty:
                    st.info("No published values for this direction and selection.")
                    continue
                for unit, group in published_rows.groupby("Unit"):
                    plot_frame = group.copy()
                    plot_frame["Published year"] = plot_frame["Year"].astype(str)
                    fig = px.scatter(
                        plot_frame, x="Published year", y="Value", color="Connection point",
                        category_orders={"Published year": [str(y) for y in outlook_years]},
                        hover_data=["Observation ID", "Source capture UTC", "Source URL"],
                        labels={"Value": f"Published indicative capacity ({unit})"},
                        color_discrete_sequence=PALETTE,
                    )
                    fig.update_traces(marker={"size": 11, "line": {"width": 1, "color": "white"}})
                    st.plotly_chart(style_plot(fig, height=385), width="stretch")
                    st.caption(f"{outlook_direction.capitalize()} · {unit}. Markers are not connected or interpolated.")
            with st.expander("Point-year evidence and source links"):
                st.dataframe(outlook, hide_index=True, width="stretch",
                             column_config={"Source URL": st.column_config.LinkColumn("Source")})
            st.download_button("Download comparison and missing-data statuses (CSV)",
                               outlook.to_csv(index=False),
                               "grid-scope-capacity-outlook.csv", "text/csv")
        else:
            st.info("Select at least one substation and one year to compare.")
        st.divider()
        st.markdown("#### Independent source recheck")
        st.warning("All 18 ORIGINAL Grid Scope figures have a dated screenshot comparison ledger (17 exact tooltips and 1 panel-value match). This blank CSV checklist starts pending for a NEW review; the original sample data remain unchanged.")
        if audit_checklist:
            st.download_button("Download independent recheck checklist (CSV)",
                               pd.DataFrame(audit_checklist).to_csv(index=False),
                               "grid-scope-independent-recheck.csv", "text/csv")
        st.caption("To recheck values, independently reopen the source viewer, confirm the direction/year/unit and record a new check time plus evidence. A changed live value need not mean the historical transcription was wrong.")

with context_tab:
    render_section(
        st, "Finland-wide context · authenticated sources",
        "What the national system was doing.",
        "Fingrid and ENTSO-E report national/bidding-zone operational series. "
        "These measurements are not observations at the selected substations "
        "and cannot be converted into available connection headroom.",
    )
    if context.empty:
        st.info("Fingrid and ENTSO-E load authenticated API smoke checks have passed, but this local database has no retained operational rows. Configure both secrets privately and run the persistent importer in docs/LIVE_CONTEXT_IMPORT.md.")
        st.code("python -m src.sync_context --day 2026-10-14")
    else:
        st.caption("These are source-described UTC intervals and retrieval revisions, not substation telemetry. ENTSO-E A03 blocks can have variable duration.")
        summary = (context.groupby(["source", "dataset_id", "metric", "unit"], dropna=False)
                   .agg(records=("value", "count"), earliest_utc=("timestamp_utc", "min"),
                        latest_utc=("interval_end_utc", "max"),
                        last_retrieved_utc=("retrieved_at", "max"))
                   .reset_index())
        st.dataframe(summary, hide_index=True, width="stretch")
        series_options = context[["source", "dataset_id", "metric", "unit"]].drop_duplicates()
        choices = list(series_options.itertuples(index=False, name=None))
        chosen = st.selectbox("Operational series", choices, format_func=lambda x: " / ".join(x))
        frame = context.copy()
        for field, value in zip(["source", "dataset_id", "metric", "unit"], chosen):
            frame = frame[frame[field] == value]
        st.caption(f"Latest retrieval: {frame.retrieved_at.max()} · UTC intervals · latest retrieved revision per interval")
        fig = px.scatter(
            frame, x="timestamp_utc", y="value",
            labels={"value": chosen[3], "timestamp_utc": "Source interval (UTC)"},
            hover_data=["interval_end_utc", "source_url"],
            color_discrete_sequence=[PALETTE[0]],
        )
        fig.update_traces(marker={"size": 7, "opacity": 0.85})
        st.plotly_chart(style_plot(fig, height=435, legend=False), width="stretch")
        st.dataframe(frame, hide_index=True)

with project_tab:
    render_section(
        st, "Evidence not yet compiled",
        "Planned reinforcements require their own sources.",
        "A planned commissioning date is uncertain and cannot establish "
        "a guaranteed MW release. This is a documentation gap, not a value of zero.",
    )
    if projects.empty:
        st.info("No project-to-substation relationships have been source-verified in this release.")
    else:
        st.dataframe(projects, hide_index=True)

with evidence_tab:
    render_section(
        st, "Provenance · verification · method",
        "What each record can, and cannot, establish.",
        "Separate published source estimates, observed operations, scenario "
        "outputs and documentary operator confirmations.",
    )
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
    st.caption("Hosted PostgreSQL (read-only dashboard connection)" if hosted else f"SQLite: {db_path()}")
    st.markdown("[Grid Scope](https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/) · "
                "[Fingrid Open Data](https://data.fingrid.fi/en/instructions) · "
                "[ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)")
    st.write("Source transcriptions and internal data-integrity checks do not validate the operator's estimates against network studies. See docs/SOURCES.md for capture provenance and reuse terms.")
    st.markdown("National operational attribution: [Fingrid Open Data](https://data.fingrid.fi/en/about), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/), source terms apply. Records are normalized from published intervals; no physical substation inference.")
    with st.expander("Model-derived scenarios (optional stretch)"):
        if scenarios.empty:
            st.info("No model runs have been performed. PyPSA and pandapower are outside this release.")
        else:
            st.warning("Assumption-dependent model output; never a published connection estimate.")
            st.dataframe(scenarios, hide_index=True)

render_footer(st)
