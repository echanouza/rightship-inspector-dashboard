from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
from processor import load_reports

st.set_page_config(page_title="RightShip Inspector Performance", page_icon="🚢", layout="wide")

st.title("RightShip Inspector Performance Dashboard")
st.caption("Internal HSQE analytics • Data is read from the configured reports folder")

with st.sidebar:
    st.header("Data source")
    default_folder = os.getenv("RIGHTSHIP_REPORTS_DIR", "./reports")
    folder = st.text_input("Reports folder path", value=default_folder)
    st.caption("On the hosted server, configure this as the shared company folder path.")
    refresh = st.button("Refresh data", type="primary")
    st.divider()
    st.caption("Supported inputs: Excel, CSV, PDF and Word. Extraction quality depends on report layout.")

@st.cache_data(ttl=60, show_spinner="Reading reports and extracting data…")
def get_data(folder_path):
    return load_reports(Path(folder_path))

if refresh:
    st.cache_data.clear()

try:
    inspections, findings, files_df, warnings = get_data(folder)
except Exception as exc:
    st.error(f"Could not read the configured folder: {exc}")
    st.info("Check the folder path and permissions. See README.md for setup.")
    st.stop()

if warnings:
    with st.expander(f"Processing notes ({len(warnings)})", expanded=False):
        for warning in warnings:
            st.write(f"• {warning}")

if inspections.empty:
    st.warning("No inspection records could be extracted yet. Add reports to the folder and review the file-processing notes.")
    if not files_df.empty:
        st.subheader("Files detected")
        st.dataframe(files_df, use_container_width=True, hide_index=True)
    st.stop()

# Normalize fields and let users filter
for col in ["inspector", "location", "vessel", "source_file"]:
    if col not in inspections:
        inspections[col] = "Unknown"
    inspections[col] = inspections[col].fillna("Unknown").astype(str).replace("", "Unknown")
if "inspection_date" not in inspections:
    inspections["inspection_date"] = pd.NaT
inspections["inspection_date"] = pd.to_datetime(inspections["inspection_date"], errors="coerce")
if "finding_count" not in inspections:
    inspections["finding_count"] = 0
inspections["finding_count"] = pd.to_numeric(inspections["finding_count"], errors="coerce").fillna(0)

with st.sidebar:
    inspectors = sorted(inspections["inspector"].unique().tolist())
    locations = sorted(inspections["location"].unique().tolist())
    vessels = sorted(inspections["vessel"].unique().tolist())
    chosen_inspectors = st.multiselect("Inspector", inspectors, default=inspectors)
    chosen_locations = st.multiselect("Inspection location", locations, default=locations)
    chosen_vessels = st.multiselect("Vessel", vessels, default=vessels)

filtered = inspections[
    inspections["inspector"].isin(chosen_inspectors)
    & inspections["location"].isin(chosen_locations)
    & inspections["vessel"].isin(chosen_vessels)
].copy()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Inspections", f"{len(filtered):,}")
c2.metric("Inspectors", f"{filtered['inspector'].nunique():,}")
c3.metric("Locations", f"{filtered['location'].nunique():,}")
c4.metric("Avg. findings / inspection", f"{filtered['finding_count'].mean():.1f}" if len(filtered) else "—")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Inspector performance", "Locations", "Data quality"])

with tab1:
    left, right = st.columns(2)
    with left:
        loc = filtered.groupby("location", as_index=False).agg(
            inspections=("source_file", "count"),
            findings=("finding_count", "sum"),
            avg_findings=("finding_count", "mean")
        ).sort_values("inspections", ascending=False)
        st.plotly_chart(px.bar(loc, x="location", y="inspections", title="Inspections by location",
                               labels={"location":"Inspection location","inspections":"Inspections"}), use_container_width=True)
    with right:
        insp = filtered.groupby("inspector", as_index=False).agg(
            inspections=("source_file", "count"),
            avg_findings=("finding_count", "mean")
        ).sort_values("avg_findings", ascending=False)
        st.plotly_chart(px.bar(insp, x="inspector", y="avg_findings", title="Average findings per inspection",
                               labels={"inspector":"Inspector","avg_findings":"Avg. findings"}), use_container_width=True)
    if filtered["inspection_date"].notna().any():
        timeline = filtered.dropna(subset=["inspection_date"]).groupby(
            filtered.dropna(subset=["inspection_date"])["inspection_date"].dt.to_period("M").astype(str)
        ).size().reset_index(name="inspections")
        timeline.columns = ["month", "inspections"]
        st.plotly_chart(px.line(timeline, x="month", y="inspections", markers=True, title="Inspection trend over time"),
                        use_container_width=True)

with tab2:
    performance = filtered.groupby("inspector", as_index=False).agg(
        inspections=("source_file", "count"),
        total_findings=("finding_count", "sum"),
        avg_findings=("finding_count", "mean"),
        locations=("location", "nunique"),
        vessels=("vessel", "nunique")
    ).sort_values(["avg_findings", "inspections"], ascending=[False, False])
    st.dataframe(performance.round({"avg_findings": 2}), use_container_width=True, hide_index=True)
    st.caption("A higher finding count does not by itself mean an inspector is stricter; compare similar inspection types and vessel contexts where possible.")

with tab3:
    locations_table = filtered.groupby("location", as_index=False).agg(
        inspections=("source_file", "count"),
        inspectors=("inspector", "nunique"),
        vessels=("vessel", "nunique"),
        total_findings=("finding_count", "sum"),
        avg_findings=("finding_count", "mean")
    ).sort_values("inspections", ascending=False)
    st.dataframe(locations_table.round({"avg_findings": 2}), use_container_width=True, hide_index=True)
    st.plotly_chart(px.scatter(locations_table, x="inspections", y="avg_findings", size="total_findings",
                               hover_name="location", title="Location comparison: inspection volume vs average findings"),
                    use_container_width=True)

with tab4:
    st.subheader("Extracted inspection records")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.subheader("Files scanned")
    if files_df.empty:
        st.info("No files detected.")
    else:
        st.dataframe(files_df, use_container_width=True, hide_index=True)
    st.download_button("Download extracted inspections (CSV)", filtered.to_csv(index=False).encode("utf-8-sig"),
                       file_name="rightship_inspections.csv", mime="text/csv")
    if not findings.empty:
        st.subheader("Extracted findings")
        st.dataframe(findings, use_container_width=True, hide_index=True)
        st.download_button("Download extracted findings (CSV)", findings.to_csv(index=False).encode("utf-8-sig"),
                           file_name="rightship_findings.csv", mime="text/csv")
