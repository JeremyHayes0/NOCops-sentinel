import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="NOCOps Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data"
REPORTS_DIR = Path(__file__).parent / "reports"


@st.cache_data
def load_data():
    server_df = pd.read_csv(DATA_DIR / "server_health.csv", parse_dates=["timestamp"])
    batch_df = pd.read_csv(DATA_DIR / "batch_jobs.csv", parse_dates=["timestamp"])
    env_df = pd.read_csv(DATA_DIR / "environmental_alerts.csv", parse_dates=["timestamp"])
    incident_df = pd.read_csv(REPORTS_DIR / "sample_incident_report.csv", parse_dates=["timestamp"])
    return server_df, batch_df, env_df, incident_df


def status_badge(value: str) -> str:
    return {
        "Critical": "🔴 Critical",
        "Warning": "🟠 Warning",
        "Healthy": "🟢 Healthy",
        "Failed": "🔴 Failed",
        "Delayed": "🟠 Delayed",
        "Success": "🟢 Success",
        "Open": "🔴 Open",
        "Escalated": "🟣 Escalated",
        "Monitoring": "🟡 Monitoring",
        "Resolved": "🟢 Resolved",
        "Medium": "🟠 Medium",
        "Low": "🟢 Low",
    }.get(str(value), str(value))


server_df, batch_df, env_df, incident_df = load_data()

st.title("NOCOps Sentinel")
st.caption("NOC, production control, and data center infrastructure monitoring dashboard")

st.markdown(
    """
    **NOCOps Sentinel** is a portfolio-grade monitoring project that simulates real computer operations work:
    server health checks, TPE/BPE production job monitoring, SLA risk detection, environmental alerts,
    and ITIL-style incident reporting.
    """
)

# Sidebar
st.sidebar.header("Filters")

min_date = min(server_df["timestamp"].min(), batch_df["timestamp"].min(), incident_df["timestamp"].min()).date()
max_date = max(server_df["timestamp"].max(), batch_df["timestamp"].max(), incident_df["timestamp"].max()).date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if len(date_range) == 2:
    start_date, end_date = date_range
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1)
else:
    start_ts = pd.Timestamp(min_date)
    end_ts = pd.Timestamp(max_date) + pd.Timedelta(days=1)

sites = st.sidebar.multiselect("Site", sorted(server_df["site"].unique()), default=sorted(server_df["site"].unique()))
server_statuses = st.sidebar.multiselect("Server status", sorted(server_df["status"].unique()), default=sorted(server_df["status"].unique()))
job_statuses = st.sidebar.multiselect("Job status", sorted(batch_df["status"].unique()), default=sorted(batch_df["status"].unique()))
incident_severities = st.sidebar.multiselect(
    "Incident severity",
    sorted(incident_df["severity"].unique()),
    default=sorted(incident_df["severity"].unique()),
)

server_filtered = server_df[
    (server_df["timestamp"] >= start_ts)
    & (server_df["timestamp"] < end_ts)
    & (server_df["site"].isin(sites))
    & (server_df["status"].isin(server_statuses))
]
batch_filtered = batch_df[
    (batch_df["timestamp"] >= start_ts)
    & (batch_df["timestamp"] < end_ts)
    & (batch_df["status"].isin(job_statuses))
]
env_filtered = env_df[(env_df["timestamp"] >= start_ts) & (env_df["timestamp"] < end_ts)]
incident_filtered = incident_df[
    (incident_df["timestamp"] >= start_ts)
    & (incident_df["timestamp"] < end_ts)
    & (incident_df["severity"].isin(incident_severities))
]

# Metrics
critical_servers = int((server_filtered["status"] == "Critical").sum())
warning_servers = int((server_filtered["status"] == "Warning").sum())
failed_jobs = int((batch_filtered["status"] == "Failed").sum())
sla_risks = int(batch_filtered["sla_risk"].sum())
critical_alerts = int((env_filtered["severity"] == "Critical").sum()) if not env_filtered.empty else 0
open_incidents = int((incident_filtered["status"] == "Open").sum())

metric_cols = st.columns(6)
metric_cols[0].metric("Critical Servers", critical_servers)
metric_cols[1].metric("Warning Servers", warning_servers)
metric_cols[2].metric("Failed Jobs", failed_jobs)
metric_cols[3].metric("SLA Risks", sla_risks)
metric_cols[4].metric("Critical Facility Alerts", critical_alerts)
metric_cols[5].metric("Open Incidents", open_incidents)

st.divider()

tab_overview, tab_servers, tab_jobs, tab_facilities, tab_incidents, tab_about = st.tabs(
    ["Operations Overview", "Server Health", "TPE/BPE Jobs", "Facilities", "Incident Queue", "Project Story"]
)

with tab_overview:
    st.subheader("Operations Command View")
    left, right = st.columns(2)

    with left:
        status_counts = server_filtered["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.bar(status_counts, x="status", y="count", title="Server Status Distribution", text="count")
        st.plotly_chart(fig, use_container_width=True)

        incident_counts = incident_filtered["severity"].value_counts().reset_index()
        incident_counts.columns = ["severity", "count"]
        fig = px.pie(incident_counts, names="severity", values="count", title="Incident Severity Mix")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        job_counts = batch_filtered["status"].value_counts().reset_index()
        job_counts.columns = ["status", "count"]
        fig = px.bar(job_counts, x="status", y="count", title="Production Job Status", text="count")
        st.plotly_chart(fig, use_container_width=True)

        hourly = incident_filtered.copy()
        if not hourly.empty:
            hourly["hour"] = hourly["timestamp"].dt.floor("h")
            hourly_counts = hourly.groupby("hour").size().reset_index(name="incident_count")
            fig = px.line(hourly_counts, x="hour", y="incident_count", markers=True, title="Incident Volume Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No incident records match the current filters.")

    st.info(
        "Use this screen like a shift handoff: review critical servers, failed production jobs, SLA risks, "
        "environmental alerts, and open incidents before drilling into the tabs."
    )

with tab_servers:
    st.subheader("Distributed Server Health")
    server_display = server_filtered.copy()
    server_display["status"] = server_display["status"].apply(status_badge)
    st.dataframe(server_display.sort_values(["timestamp", "status"]), use_container_width=True, hide_index=True)

    avg_util = (
        server_filtered.groupby("os")[["cpu_usage", "memory_usage", "disk_usage", "latency_ms"]]
        .mean()
        .round(1)
        .reset_index()
    )
    fig = px.bar(avg_util, x="os", y=["cpu_usage", "memory_usage", "disk_usage"], barmode="group", title="Average Utilization by OS")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### High-Risk Server Events")
    risky = server_filtered[server_filtered["status"].isin(["Critical", "Warning"])].sort_values("timestamp", ascending=False)
    st.dataframe(risky, use_container_width=True, hide_index=True)

with tab_jobs:
    st.subheader("TPE/BPE Production Control")
    job_display = batch_filtered.copy()
    job_display["status"] = job_display["status"].apply(status_badge)
    st.dataframe(job_display.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)

    col_a, col_b = st.columns(2)
    with col_a:
        sla_summary = batch_filtered.groupby("job_type")["sla_risk"].mean().mul(100).round(1).reset_index()
        fig = px.bar(sla_summary, x="job_type", y="sla_risk", title="SLA Risk Rate by Job Type (%)", text="sla_risk")
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        duration = batch_filtered.groupby("job_name")["duration_minutes"].mean().round(1).reset_index()
        fig = px.bar(duration, x="duration_minutes", y="job_name", orientation="h", title="Average Job Duration")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Jobs Requiring Follow-Up")
    st.dataframe(batch_filtered[batch_filtered["sla_risk"]].sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)

with tab_facilities:
    st.subheader("Environmental & Facility Systems")
    if env_filtered.empty:
        st.success("No environmental alerts match the selected date range.")
    else:
        env_display = env_filtered.copy()
        env_display["severity"] = env_display["severity"].apply(status_badge)
        env_display["status"] = env_display["status"].apply(status_badge)
        st.dataframe(env_display.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)

        col_a, col_b = st.columns(2)
        with col_a:
            fig = px.bar(env_filtered["system_type"].value_counts().reset_index(), x="system_type", y="count", title="Alerts by System Type", text="count")
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            fig = px.bar(env_filtered["severity"].value_counts().reset_index(), x="severity", y="count", title="Facility Alert Severity", text="count")
            st.plotly_chart(fig, use_container_width=True)

with tab_incidents:
    st.subheader("ITIL-Style Incident Queue")
    incident_display = incident_filtered.copy()
    incident_display["severity"] = incident_display["severity"].apply(status_badge)
    incident_display["status"] = incident_display["status"].apply(status_badge)
    st.dataframe(incident_display.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)

    csv = incident_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Filtered Incident Report",
        csv,
        file_name="nocops_incident_report.csv",
        mime="text/csv",
    )

with tab_about:
    st.subheader("Why this project matters")
    st.markdown(
        """
        This app is built to speak directly to NOC, computer operations, production control, data center,
        and security operations roles.

        **Skills demonstrated**
        - Server health monitoring across Windows, Linux, and AIX-style systems
        - TPE/BPE job monitoring and SLA-risk tracking
        - UPS, generator, HVAC, fire suppression, and physical security alert awareness
        - ITIL-style incident classification and operational handoff reporting
        - Python, pandas, Streamlit, Plotly, CSV reporting, and dashboard deployment

        **Resume bullet**
        > Built a Python and Streamlit NOC monitoring dashboard simulating server health checks,
        production control workflows, TPE/BPE SLA-risk detection, data center environmental alerts,
        and ITIL-style incident response reporting.
        """
    )

st.caption("NOCOps Sentinel | NOC Operations • Production Control • Data Center Infrastructure • Security Operations")
