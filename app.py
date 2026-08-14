import json
import pandas as pd
import streamlit as st
import folium
import plotly.express as px

from streamlit_folium import st_folium


# ==================================================
# PAGE SETTINGS
# ==================================================

st.set_page_config(
    page_title="AEGIS | Stem Borer Dashboard",
    page_icon="🌾",
    layout="wide"
)


# ==================================================
# LOAD GEOJSON
# ==================================================

with open("norala_barangay.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)


# ==================================================
# PREPARE DATAFRAME
# ==================================================

records = []

for feature in geojson_data["features"]:
    p = feature["properties"]

    records.append({
        "Barangay": p.get("NAME_3"),
        "Total Reports": float(p.get("Total_Repo", 0) or 0),
        "Affected Area (ha)": float(p.get("Affected_A", 0) or 0),
        "Severity (%)": float(p.get("Severity", 0) or 0),
        "IPI": float(p.get("IPI", 0) or 0)
    })

df = pd.DataFrame(records)


# ==================================================
# PRIORITY CLASSIFICATION
# ==================================================

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

priority_lookup = dict(zip(df["Barangay"], df["Priority"]))

for feature in geojson_data["features"]:
    barangay = feature["properties"].get("NAME_3")
    feature["properties"]["Priority"] = priority_lookup.get(
        barangay,
        "No reported infestation"
    )


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.title("🌾 AEGIS")

    st.markdown(
        """
        **Agricultural Geospatial Intelligence System**

        AEGIS is a web-based geospatial dashboard developed to visualize
        reported **stem borer infestation in Norala, South Cotabato for 2025**.

        The dashboard presents four indicators:

        - Report frequency
        - Affected rice area
        - Mean damage severity
        - Infestation Priority Index (IPI)
        """
    )

    st.divider()

    st.subheader("About the IPI")

    st.markdown(
        """
        The **Infestation Priority Index (IPI)** combines:

        **Report Frequency + Affected Area + Severity**

        Each indicator was normalized from **0 to 1** and given equal weight.

        Higher IPI values indicate greater relative priority for stem borer
        monitoring and management.
        """
    )

    st.divider()

    st.caption(
        "Data source: Municipal Agriculture Office (MAO), Norala, 2025"
    )


# ==================================================
# HEADER
# ==================================================

st.title("🌾 AEGIS")

st.subheader(
    "Web-Based Geospatial Dashboard for Stem Borer Infestation "
    "in Norala, South Cotabato"
)

st.caption(
    "Barangay-level visualization of reported stem borer infestation data for 2025"
)


# ==================================================
# SUMMARY CARDS
# ==================================================

affected = df[df["Total Reports"] > 0]

total_reports = int(df["Total Reports"].sum())
total_area = df["Affected Area (ha)"].sum()
affected_barangays = len(affected)

highest_row = affected.loc[affected["IPI"].idxmax()]

highest_barangay = highest_row["Barangay"]
highest_ipi = highest_row["IPI"]


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Reports",
        f"{total_reports}"
    )

with col2:
    st.metric(
        "Affected Rice Area",
        f"{total_area:.2f} ha"
    )

with col3:
    st.metric(
        "Affected Barangays",
        f"{affected_barangays}"
    )

with col4:
    st.metric(
        "Highest IPI",
        f"{highest_barangay}"
    )
    st.caption(f"IPI = {highest_ipi:.3f}")


st.divider()


# ==================================================
# MAP SECTION
# ==================================================

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


# ==================================================
# COLOR CLASSIFICATION
# ==================================================

def get_color(value, field):

    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0

    # No infestation
    if value == 0:
        return "#eeeeee"

    # REPORT FREQUENCY
    if field == "Total_Repo":

        if value <= 5:
            return "#fee5d9"
        elif value <= 10:
            return "#fcae91"
        elif value <= 20:
            return "#fb6a4a"
        else:
            return "#cb181d"

    # AFFECTED AREA
    elif field == "Affected_A":

        if value <= 10:
            return "#fee5d9"
        elif value <= 20:
            return "#fcae91"
        elif value <= 40:
            return "#fb6a4a"
        else:
            return "#cb181d"

    # SEVERITY
    elif field == "Severity":

        if value <= 20:
            return "#fee5d9"
        elif value <= 40:
            return "#fcae91"
        elif value <= 60:
            return "#fb6a4a"
        else:
            return "#cb181d"

    # IPI
    elif field == "IPI":

        if value <= 0.20:
            return "#fee5d9"
        elif value <= 0.40:
            return "#fcae91"
        elif value <= 0.60:
            return "#fb6a4a"
        else:
            return "#cb181d"

    return "#eeeeee"


# ==================================================
# DYNAMIC LEGEND
# ==================================================

if indicator == "Total Reports":

    legend_title = "Number of Reported Infestations"

    legend_items = [
        ("#eeeeee", "No reported infestation"),
        ("#fee5d9", "Low: 1–5 reports"),
        ("#fcae91", "Moderate: 6–10 reports"),
        ("#fb6a4a", "High: 11–20 reports"),
        ("#cb181d", "Very High: 21–40 reports")
    ]

elif indicator == "Affected Area (ha)":

    legend_title = "Affected Rice Area"

    legend_items = [
        ("#eeeeee", "No reported affected area"),
        ("#fee5d9", "0.1–10 ha"),
        ("#fcae91", "10.1–20 ha"),
        ("#fb6a4a", "20.1–40 ha"),
        ("#cb181d", "40.1 ha and above")
    ]

elif indicator == "Severity (%)":

    legend_title = "Mean Damage Severity"

    legend_items = [
        ("#eeeeee", "No reported infestation"),
        ("#fee5d9", "0.1–20%"),
        ("#fcae91", "20.1–40%"),
        ("#fb6a4a", "40.1–60%"),
        ("#cb181d", "60.1–80%")
    ]

else:

    legend_title = "Infestation Priority Index"

    legend_items = [
        ("#eeeeee", "No reported infestation"),
        ("#fee5d9", "Low: 0.001–0.200"),
        ("#fcae91", "Moderate: 0.201–0.400"),
        ("#fb6a4a", "High: 0.401–0.600"),
        ("#cb181d", "Very High: 0.601–1.000")
    ]


legend_html = f"""
<div style="padding:14px; border:1px solid #555; border-radius:8px; margin-bottom:15px;">
    <div style="font-weight:700; margin-bottom:12px;">{legend_title}</div>
"""

for color, label in legend_items:
    legend_html += (
        f'<div style="display:flex; align-items:center; margin-bottom:7px;">'
        f'<span style="display:inline-block; width:18px; height:18px; '
        f'background-color:{color}; border:1px solid #777; '
        f'margin-right:10px;"></span>'
        f'<span>{label}</span>'
        f'</div>'
    )

legend_html += "</div>"

st.markdown(legend_html, unsafe_allow_html=True)

# ==================================================
# CREATE MAP
# ==================================================

m = folium.Map(
    location=[6.52, 124.68],
    zoom_start=12,
    tiles="CartoDB positron"
)


def style_function(feature):

    value = feature["properties"].get(selected_field, 0)

    return {
        "fillColor": get_color(value, selected_field),
        "color": "#333333",
        "weight": 1.2,
        "fillOpacity": 0.80
    }


def highlight_function(feature):

    return {
        "weight": 3,
        "color": "#000000",
        "fillOpacity": 0.90
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
    sticky=True,
    labels=True
)


folium.GeoJson(
    geojson_data,
    name="Stem Borer Infestation",
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=tooltip
).add_to(m)


# Automatically fit map to municipality
all_coordinates = []

for feature in geojson_data["features"]:

    geometry = feature["geometry"]

    if geometry["type"] == "Polygon":

        for ring in geometry["coordinates"]:
            for lon, lat in ring:
                all_coordinates.append([lat, lon])

    elif geometry["type"] == "MultiPolygon":

        for polygon in geometry["coordinates"]:
            for ring in polygon:
                for lon, lat in ring:
                    all_coordinates.append([lat, lon])


if all_coordinates:

    lats = [x[0] for x in all_coordinates]
    lons = [x[1] for x in all_coordinates]

    bounds = [
        [min(lats), min(lons)],
        [max(lats), max(lons)]
    ]

    m.fit_bounds(bounds)


st_folium(
    m,
    height=620,
    use_container_width=True
)

st.caption(
    "Hover over a barangay to view its infestation statistics."
)


# ==================================================
# BARANGAY ANALYSIS
# ==================================================

st.divider()

st.header("Barangay-Level Analysis")


# REPORTS
reports_df = affected.sort_values(
    "Total Reports",
    ascending=True
)

fig_reports = px.bar(
    reports_df,
    x="Total Reports",
    y="Barangay",
    orientation="h",
    title="Number of Reported Stem Borer Infestations by Barangay"
)

fig_reports.update_layout(
    yaxis_title="",
    xaxis_title="Number of Reports"
)

st.plotly_chart(
    fig_reports,
    use_container_width=True
)


# AFFECTED AREA
area_df = affected.sort_values(
    "Affected Area (ha)",
    ascending=True
)

fig_area = px.bar(
    area_df,
    x="Affected Area (ha)",
    y="Barangay",
    orientation="h",
    title="Total Rice Area Affected by Stem Borer"
)

fig_area.update_layout(
    yaxis_title="",
    xaxis_title="Affected Rice Area (ha)"
)

st.plotly_chart(
    fig_area,
    use_container_width=True
)


# SEVERITY
severity_df = affected.sort_values(
    "Severity (%)",
    ascending=True
)

fig_severity = px.bar(
    severity_df,
    x="Severity (%)",
    y="Barangay",
    orientation="h",
    title="Mean Stem Borer Damage Severity by Barangay"
)

fig_severity.update_xaxes(
    range=[0, 100]
)

fig_severity.update_layout(
    yaxis_title="",
    xaxis_title="Mean Damage Severity (%)"
)

st.plotly_chart(
    fig_severity,
    use_container_width=True
)


# ==================================================
# PRIORITY RANKING
# ==================================================

st.divider()

st.header("Infestation Priority Ranking")

priority_df = affected.sort_values(
    "IPI",
    ascending=False
)[
    [
        "Barangay",
        "Total Reports",
        "Affected Area (ha)",
        "Severity (%)",
        "IPI",
        "Priority"
    ]
]

priority_df["IPI"] = priority_df["IPI"].round(3)

st.dataframe(
    priority_df,
    use_container_width=True,
    hide_index=True
)
# ==================================================
# ADD NEW REPORT
# ==================================================

st.divider()

st.header("Report Stem Borer Infestation")

st.caption(
    "Use this form to encode a new reported stem borer infestation."
)

if "submitted_reports" not in st.session_state:
    st.session_state.submitted_reports = []

with st.form("report_form", clear_on_submit=True):

    col1, col2 = st.columns(2)

    with col1:
        report_date = st.date_input("Date observed")

        report_barangay = st.selectbox(
            "Barangay",
            sorted(df["Barangay"].unique())
        )

    with col2:
        affected_area = st.number_input(
            "Affected rice area (ha)",
            min_value=0.0,
            step=0.1
        )

        severity = st.number_input(
            "Estimated damage severity (%)",
            min_value=0.0,
            max_value=100.0,
            step=1.0
        )

    remarks = st.text_area(
        "Remarks / observation",
        placeholder="Describe the observed infestation..."
    )

    submitted = st.form_submit_button(
        "Submit Report",
        type="primary"
    )

    if submitted:

        new_report = {
            "Date Observed": str(report_date),
            "Barangay": report_barangay,
            "Affected Area (ha)": affected_area,
            "Severity (%)": severity,
            "Remarks": remarks
        }

        st.session_state.submitted_reports.append(new_report)

        st.success(
            f"Report for {report_barangay} was successfully submitted."
        )


if st.session_state.submitted_reports:

    st.subheader("Submitted Reports")

    report_df = pd.DataFrame(
        st.session_state.submitted_reports
    )

    st.dataframe(
        report_df,
        use_container_width=True,
        hide_index=True
    )

    csv = report_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Submitted Reports",
        data=csv,
        file_name="aegis_submitted_reports.csv",
        mime="text/csv"
    )

# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "Source: Municipal Agriculture Office (MAO), Norala, South Cotabato, 2025. "
    "AEGIS is a visualization and decision-support prototype based on available "
    "2025 barangay-level stem borer infestation records."
)
