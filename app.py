import json
import pandas as pd
import streamlit as st
import folium
import plotly.express as px

from streamlit_folium import st_folium


# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------

st.set_page_config(
    page_title="AEGIS | Stem Borer Dashboard",
    page_icon="🌾",
    layout="wide"
)


# --------------------------------------------------
# LOAD GEOJSON DATA
# --------------------------------------------------

with open("norala_barangay.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)


# --------------------------------------------------
# CONVERT GEOJSON ATTRIBUTES TO DATAFRAME
# --------------------------------------------------

records = []

for feature in geojson_data["features"]:
    p = feature["properties"]

    records.append({
        "Barangay": p.get("NAME_3"),
        "Total Reports": p.get("Total_Repo", 0),
        "Affected Area (ha)": p.get("Affected_A", 0),
        "Severity (%)": p.get("Severity", 0),
        "IPI": p.get("IPI", 0)
    })

df = pd.DataFrame(records)


# --------------------------------------------------
# PRIORITY CLASSIFICATION
# --------------------------------------------------

def classify_priority(ipi):
    if ipi == 0:
        return "No reported infestation"
    elif ipi <= 0.20:
        return "Low"
    elif ipi <= 0.40:
        return "Moderate"
    elif ipi <= 0.60:
        return "High"
    else:
        return "Very High"


df["Priority"] = df["IPI"].apply(classify_priority)


# Add priority back to GeoJSON for map tooltip
priority_lookup = dict(zip(df["Barangay"], df["Priority"]))

for feature in geojson_data["features"]:
    barangay = feature["properties"].get("NAME_3")
    feature["properties"]["Priority"] = priority_lookup.get(
        barangay,
        "No reported infestation"
    )


# --------------------------------------------------
# DASHBOARD HEADER
# --------------------------------------------------

st.title("🌾 AEGIS")
st.subheader(
    "Web-Based Geospatial Dashboard for Stem Borer Infestation "
    "in Norala, South Cotabato"
)

st.caption(
    "Visualization of reported stem borer infestation data for 2025"
)


# --------------------------------------------------
# SUMMARY STATISTICS
# --------------------------------------------------

affected = df[df["Total Reports"] > 0]

total_reports = int(df["Total Reports"].sum())
total_area = df["Affected Area (ha)"].sum()
affected_barangays = len(affected)

if not affected.empty:
    highest_priority = affected.loc[affected["IPI"].idxmax(), "Barangay"]
else:
    highest_priority = "None"


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Reports", f"{total_reports}")

with col2:
    st.metric("Affected Rice Area", f"{total_area:.2f} ha")

with col3:
    st.metric("Affected Barangays", f"{affected_barangays}")

with col4:
    st.metric("Highest Priority", highest_priority)


st.divider()


# --------------------------------------------------
# INTERACTIVE MAP
# --------------------------------------------------

st.header("Interactive Stem Borer Infestation Map")

indicator = st.selectbox(
    "Select map indicator",
    [
        "Total Reports",
        "Affected Area (ha)",
        "Severity (%)",
        "Infestation Priority Index"
    ]
)


field_dictionary = {
    "Total Reports": "Total_Repo",
    "Affected Area (ha)": "Affected_A",
    "Severity (%)": "Severity",
    "Infestation Priority Index": "IPI"
}

selected_field = field_dictionary[indicator]


# Create map centered on Norala
m = folium.Map(
    location=[6.52, 124.68],
    zoom_start=12,
    tiles="OpenStreetMap"
)


# Color functions
def get_color(value, field):
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0

    if value == 0:
        return "#f2f2f2"

    if field == "Total_Repo":
        if value <= 5:
            return "#fde0dd"
        elif value <= 10:
            return "#fa9fb5"
        elif value <= 20:
            return "#f768a1"
        else:
            return "#ae017e"

    elif field == "Affected_A":
        if value <= 10:
            return "#fee5d9"
        elif value <= 20:
            return "#fcae91"
        elif value <= 40:
            return "#fb6a4a"
        else:
            return "#cb181d"

    elif field == "Severity":
        if value <= 20:
            return "#fee5d9"
        elif value <= 40:
            return "#fcae91"
        elif value <= 60:
            return "#fb6a4a"
        else:
            return "#cb181d"

    elif field == "IPI":
        if value <= 0.20:
            return "#fee5d9"
        elif value <= 0.40:
            return "#fcae91"
        elif value <= 0.60:
            return "#fb6a4a"
        else:
            return "#cb181d"

    return "#f2f2f2"


def style_function(feature):
    value = feature["properties"].get(selected_field, 0)

    return {
        "fillColor": get_color(value, selected_field),
        "color": "#333333",
        "weight": 1,
        "fillOpacity": 0.75
    }


tooltip = folium.GeoJsonTooltip(
    fields=[
        "NAME_3",
        "Total_Repo",
        "Affected_A",
        "Severity",
        "IPI",
        "Priority"
    ],
    aliases=[
        "Barangay:",
        "Total Reports:",
        "Affected Area (ha):",
        "Mean Severity (%):",
        "IPI:",
        "Priority:"
    ],
    localize=True,
    sticky=False,
    labels=True
)


folium.GeoJson(
    geojson_data,
    name="Stem Borer Data",
    style_function=style_function,
    tooltip=tooltip
).add_to(m)


folium.LayerControl().add_to(m)


st_folium(
    m,
    width=None,
    height=600,
    use_container_width=True
)


st.caption(
    "Hover over a barangay to view its reported infestation statistics."
)


# --------------------------------------------------
# BARANGAY ANALYSIS
# --------------------------------------------------

st.divider()

st.header("Barangay-Level Analysis")

affected_sorted_reports = affected.sort_values(
    "Total Reports",
    ascending=True
)

fig_reports = px.bar(
    affected_sorted_reports,
    x="Total Reports",
    y="Barangay",
    orientation="h",
    title="Number of Reported Stem Borer Infestations by Barangay",
    labels={"Total Reports": "Number of Reports"}
)

st.plotly_chart(fig_reports, use_container_width=True)


affected_sorted_area = affected.sort_values(
    "Affected Area (ha)",
    ascending=True
)

fig_area = px.bar(
    affected_sorted_area,
    x="Affected Area (ha)",
    y="Barangay",
    orientation="h",
    title="Total Rice Area Affected by Stem Borer",
    labels={"Affected Area (ha)": "Affected Area (ha)"}
)

st.plotly_chart(fig_area, use_container_width=True)


affected_sorted_severity = affected.sort_values(
    "Severity (%)",
    ascending=True
)

fig_severity = px.bar(
    affected_sorted_severity,
    x="Severity (%)",
    y="Barangay",
    orientation="h",
    title="Mean Stem Borer Damage Severity by Barangay",
    labels={"Severity (%)": "Mean Damage Severity (%)"}
)

fig_severity.update_xaxes(range=[0, 100])

st.plotly_chart(fig_severity, use_container_width=True)


# --------------------------------------------------
# DATA TABLE
# --------------------------------------------------

st.divider()

st.header("Barangay Summary")

display_df = df[
    [
        "Barangay",
        "Total Reports",
        "Affected Area (ha)",
        "Severity (%)",
        "IPI",
        "Priority"
    ]
].sort_values("IPI", ascending=False)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Data source: Municipal Agriculture Office (MAO), Norala, 2025. "
    "The Infestation Priority Index (IPI) combines normalized report "
    "frequency, affected rice area, and mean damage severity using equal weights."
)
