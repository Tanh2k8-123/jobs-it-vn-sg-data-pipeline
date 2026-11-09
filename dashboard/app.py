"""Local CSV dashboard; the same marts can be connected directly in Looker Studio."""

import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="Tech Jobs | VN × SG", page_icon="◈", layout="wide")
COLORS = {"VN": "#187e78", "SG": "#d66a38"}
st.markdown(
    """
<style>
    .block-container {max-width: 1280px; padding-top: 2.5rem;}
    h1 {font-family: Georgia, serif; letter-spacing: -.045em; font-size: 3.2rem !important;}
    [data-testid="stMetricValue"] {font-variant-numeric: tabular-nums; color: #123047;}
    [data-testid="stMetric"] {background: #fff; border-radius: 14px; padding: 16px 20px;}
    .eyebrow {color: #187e78; font: 600 12px monospace; letter-spacing: .12em;}
    :focus-visible {outline: 3px solid #187e78 !important; outline-offset: 3px;}
</style>
""",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="eyebrow">VIETNAM × SINGAPORE / OBSERVED RECRUITMENT</div>', unsafe_allow_html=True
)
st.title("Where tech teams are hiring")
st.caption("Public postings across monitored company boards. Each posting counts once per day.")

root = Path(os.getenv("DATA_DIR", "data/local")) / "dashboard"
try:
    metadata = json.loads((root / "current.json").read_text(encoding="utf-8"))
except (FileNotFoundError, ValueError):
    st.info("No observations have been published yet. Run the pipeline, then refresh this page.")
    st.code("uv run sea-it-jobs pipeline --target local", language="bash")
    st.stop()
generation = root / metadata["generation"]
if metadata.get("synthetic"):
    st.warning("Synthetic demonstration data. These observations do not describe the job market.")


@st.cache_data(ttl=60)
def read_table(path: str):
    frame = pd.read_csv(path)
    if "snapshot_date" in frame:
        frame["snapshot_date"] = pd.to_datetime(frame["snapshot_date"])
    return frame


overview = read_table(str(generation / "mart_daily_overview.csv"))
if overview.empty:
    st.info("No observed dates are available yet.")
    st.stop()
dates = sorted(overview.snapshot_date.dt.date.unique(), reverse=True)
selected = st.sidebar.selectbox("Observation date", dates)
selected_ts = pd.Timestamp(selected)
st.sidebar.caption(f"Published: {metadata['generated_at']}")
st.sidebar.markdown("**Counting rules**")
st.sidebar.caption(
    "A posting linked to both countries appears in both country counts. "
    "The overall count includes it once. Descriptions are not used to infer location."
)
if st.sidebar.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

health = read_table(str(generation / "mart_source_health.csv"))
day_health = health[health.snapshot_date == selected_ts]
row = overview[overview.snapshot_date == selected_ts].iloc[0]
successful, expected = int(row.successful_boards), int(row.expected_boards)
st.markdown(f"**Source coverage · {successful}/{expected} complete snapshots**")
source_columns = st.columns(max(len(day_health), 1))
for column, (_, source) in zip(source_columns, day_health.iterrows()):
    with column:
        symbol = "●" if source.snapshot_status == "complete" else "○"
        st.markdown(f"{symbol} **{source.company_name}**")
        latest = source.latest_attempt_status
        if source.snapshot_status == "complete":
            st.caption(f"{int(source.record_count)} board postings · latest attempt: {latest}")
        else:
            st.caption(f"Snapshot unavailable · latest attempt: {latest}")
if successful != expected:
    st.warning("Coverage is incomplete. Counts include available sources; compare dates with care.")
if int(row.failed_latest_boards) > 0:
    st.info(
        "At least one latest attempt failed. Earlier successful snapshots may still be selected."
    )

country = read_table(str(generation / "mart_daily_country.csv"))
country_day = country[country.snapshot_date == selected_ts]


def display_number(value):
    return "Unavailable" if pd.isna(value) else f"{int(value):,}"


metrics = st.columns(4)
metrics[0].metric("Distinct tech postings · VN or SG", display_number(row.tech_postings))
for column, code in zip(metrics[1:3], ["VN", "SG"]):
    value = country_day.loc[country_day.country_code == code, "tech_postings"]
    column.metric(
        f"Postings linked to {code}", display_number(value.iloc[0]) if len(value) else "Unavailable"
    )
metrics[3].metric("Companies with target tech roles", display_number(row.recruiting_companies))


def chart_layout(figure):
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#123047"},
        margin={"l": 12, "r": 12, "t": 24, "b": 12},
        legend_title_text="",
        xaxis_title=None,
        yaxis_title=None,
    )
    return figure


left, right = st.columns([1, 1.4])
with left:
    st.subheader("Two markets, shared opportunities")
    figure = px.bar(
        country_day,
        x="tech_postings",
        y="country_code",
        color="country_code",
        color_discrete_map=COLORS,
        orientation="h",
        text_auto=True,
    )
    st.plotly_chart(chart_layout(figure), width="stretch")
with right:
    st.subheader("Which roles appear most?")
    roles = read_table(str(generation / "mart_daily_roles.csv"))
    roles = roles[roles.snapshot_date == selected_ts]
    if roles.empty:
        st.info("No classified target-market technology postings on this date.")
    else:
        figure = px.bar(
            roles,
            x="tech_postings",
            y="role_category",
            color="country_code",
            color_discrete_map=COLORS,
            orientation="h",
            barmode="group",
        )
        st.plotly_chart(chart_layout(figure), width="stretch")

st.subheader("Daily observations")
if len(dates) < 2:
    st.info(
        "One real snapshot date is available. Trends will appear after the next collection day."
    )
else:
    figure = px.line(
        country.sort_values("snapshot_date"),
        x="snapshot_date",
        y="tech_postings",
        color="country_code",
        color_discrete_map=COLORS,
        markers=True,
        hover_data=["coverage_ratio"],
    )
    figure.update_traces(connectgaps=False)
    st.plotly_chart(chart_layout(figure), width="stretch")
st.caption(
    "Counts describe observed postings at selected companies. Source changes can affect "
    "day-to-day comparisons; a posting is not a count of vacancies or completed hires."
)

companies = read_table(str(generation / "mart_daily_company.csv"))
st.subheader("Company view")
st.dataframe(
    companies[companies.snapshot_date == selected_ts][
        ["company_name", "tech_postings", "snapshot_status"]
    ],
    hide_index=True,
    width="stretch",
)
with st.expander("Source status and errors"):
    st.dataframe(day_health, hide_index=True, width="stretch")
with st.expander("Download daily metrics"):
    st.download_button(
        "Download overview CSV",
        overview.to_csv(index=False),
        file_name="tech-jobs-daily-overview.csv",
        mime="text/csv",
    )
