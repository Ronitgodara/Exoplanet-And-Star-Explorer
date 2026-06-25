import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import base64
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="Exoplanet & Star Explorer",
    page_icon="🌌",
    layout="wide"
)
def set_bg(image_file):
    with open(image_file, "rb") as file:
        encoded = base64.b64encode(file.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg("space_bg.jpg")
st.markdown("""
<style>

/* Metric cards */
[data-testid="stMetric"]{
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255,255,255,0.08);
}

/* Dataframes */
.stDataFrame{
    background: transparent !important;
}

/* Plotly charts */
.stPlotlyChart{
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(12px);
    border-radius: 15px;
}

/* Selectboxes */
[data-baseweb="select"] > div{
    background: rgba(255,255,255,0.05) !important;
    backdrop-filter: blur(12px);
}

/* Main content area */
.block-container{
    background: rgba(0,0,0,0.05);
}

/* Headers */
h1,h2,h3{
    color:white !important;
}

</style>
""", unsafe_allow_html=True)

st.title("🌌 Exoplanet & Star Explorer")
st.write("Explore planets beyond our Solar System.")

# MySQL Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_pass",      # Put your MySQL password here
    database="space"
)
query = """
SELECT
    e.planet_id,
    e.planet_name,
    e.planet_type,
    e.discovery_year,
    e.discovery_method,
    e.orbital_period_days,
    e.planet_radius_earth,
    e.semi_major_axis_au,
    e.equilibrium_temp_k,
    e.planet_mass_earth,

    s.star_name,
    s.spectral_type,
    s.tempraure_k,
    s.mass_solar,
    s.radius_solar,
    s.distance_ly,
    s.age_billion_years

FROM exoplanets e
JOIN stars s
ON e.star_id = s.star_id
"""
df=pd.read_sql(query,conn)
st.divider()

st.subheader("🪐 Planet Explorer")

selected_planet = st.selectbox(
    "Select Planet",
    sorted(df["planet_name"].dropna().unique())
)

planet_data = df[df["planet_name"] == selected_planet]

st.dataframe(planet_data)
st.divider()
st.subheader("⭐ Star Explorer")

selected_star = st.selectbox(
    "Select Star",
    sorted(df["star_name"].dropna().unique())
)

star_data = df[df["star_name"] == selected_star]

st.write("### Star Information")

st.dataframe(
    star_data[
        [
            "star_name",
            "spectral_type",
            "tempraure_k",
            "mass_solar",
            "radius_solar",
            "distance_ly",
            "age_billion_years"
        ]
    ].drop_duplicates()
)

st.write("### Orbiting Planets")

st.dataframe(
    star_data[
        [
            "planet_name",
            "planet_type",
            "planet_mass_earth",
            "planet_radius_earth"
        ]
    ]
)
st.divider()

st.subheader("🥧 Planet Type Distribution")
df["planet_type"] = (
    df["planet_type"]
    .str.strip()
    .replace({
        "Terrestrial": "Terrestrial",
        "terrestrial": "Terrestrial",
        "Neptune-Like": "Neptune Like",
        "Mini-Neptune": "Mini Neptune"
    })
)

planet_counts = (
    df["planet_type"]
    .value_counts()
    .reset_index()
)

planet_counts.columns = ["planet_type", "count"]

fig = px.pie(
    planet_counts,
    names="planet_type",
    values="count",
    title="Distribution of Planet Types"
)

st.plotly_chart(fig, use_container_width=True)
st.divider()

st.subheader("📈 Discovery Timeline")

year_counts = (
    df["discovery_year"]
    .value_counts()
    .sort_index()
    .reset_index()
)

year_counts.columns = ["year", "discoveries"]

fig = px.line(
    year_counts,
    x="year",
    y="discoveries",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)
st.divider()
st.subheader("🔬 Discovery Methods")
method_counts=(
    df["discovery_method"]
    .value_counts()
    .reset_index()
)
method_counts.columns=["method","count"]
fig=px.bar(
    method_counts,
    x="method",
    y="count"
)
st.plotly_chart(fig,use_container_width=True)
st.divider()
def habitability_index(row):
    score = 0

    # Radius (40 points)
    radius = row["planet_radius_earth"]

    if 0.8 <= radius <= 1.5:
        score += 40
    elif 0.5 <= radius <= 2.0:
        score += 25
    else:
        score += 5

    # Temperature (40 points)
    temp = row["equilibrium_temp_k"]

    if 250 <= temp <= 320:
        score += 40
    elif 200 <= temp <= 350:
        score += 25
    else:
        score += 5

    # Planet Type (15 points)
    ptype = str(row["planet_type"]).lower()

    if "terrestrial" in ptype:
        score += 15
    elif "super earth" in ptype:
        score += 10
    else:
        score += 3

    # Distance from Earth (5 points)
    dist = row["distance_ly"]

    if dist <= 50:
        score += 5
    elif dist <= 100:
        score += 3
    else:
        score += 1

    return score
df["habitability_index"]=df.apply(habitability_index,axis=1)
st.subheader("🌍 Top Habitable Candidates")

best = df.sort_values(
    by="habitability_index",
    ascending=False
)

st.dataframe(
    best[
        [
            "planet_name",
            "planet_type",
            "planet_radius_earth",
            "equilibrium_temp_k",
            "distance_ly",
            "habitability_index"
        ]
    ].head(40)
)
def habitability_label(score):
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "High"
    elif score >= 50:
        return "Moderate"
    else:
        return "Low"

df["habitability_class"] = (
    df["habitability_index"]
    .apply(habitability_label)
)
habit_counts = (
    df["habitability_class"]
    .value_counts()
    .reset_index()
)

habit_counts.columns = ["class", "count"]

fig = px.pie(
    habit_counts,
    names="class",
    values="count",
    title="Habitability Classes"
)

st.plotly_chart(fig, use_container_width=True)
st.divider()
st.divider()

st.subheader("🔍 Search Planet")

search = st.text_input("Enter Planet Name")

if search:
    result = df[
        df["planet_name"]
        .str.contains(search, case=False, na=False)
    ]

    st.dataframe(result)

# Star Classification
def classify_star(temp):
    if temp >= 30000:
        return "O"
    elif temp >= 10000:
        return "B"
    elif temp >= 7500:
        return "A"
    elif temp >= 6000:
        return "F"
    elif temp >= 5200:
        return "G"
    elif temp >= 3700:
        return "K"
    else:
        return "M"

df["star_class"] = df["tempraure_k"].apply(classify_star)

st.divider()

st.subheader("⭐ Stellar Classification")

star_class_counts = (
    df["star_class"]
    .value_counts()
    .reset_index()
)

star_class_counts.columns = ["class", "count"]

fig = px.bar(
    star_class_counts,
    x="class",
    y="count",
    title="Star Classes"
)

st.plotly_chart(fig, use_container_width=True)
def planet_size(radius):
    if radius < 1.25:
        return "Earth-size"
    elif radius < 2:
        return "Super Earth"
    elif radius < 6:
        return "Neptune-like"
    else:
        return "Gas Giant"

df["size_category"] = df["planet_radius_earth"].apply(planet_size)
st.divider()

st.subheader("🪐 Planet Size Categories")

size_counts = (
    df["size_category"]
    .value_counts()
    .reset_index()
)

size_counts.columns = ["size", "count"]

fig = px.pie(
    size_counts,
    names="size",
    values="count"
)

st.plotly_chart(fig, use_container_width=True)
st.divider()

st.subheader("🌌 3D Planet Explorer")
fig=px.scatter_3d(
    df,
    x="distance_ly",
    y="planet_mass_earth",
    z="planet_radius_earth",
    color="planet_type",
    hover_name="planet_name"
)
st.plotly_chart(fig,use_container_width=True)
st.divider()
st.subheader("📍 Closest Exoplanets")
closest=(
    df.sort_values("distance_ly")
    [
        [
            "planet_name",
            "star_name",
            "distance_ly"
            ]
        ]
)
st.dataframe(closest.head(20))
            
st.subheader("⚔️ Planet Comparison")

planet1 = st.selectbox(
    "Planet 1",
    sorted(df["planet_name"].dropna().unique()),
    key="p1"
)

planet2 = st.selectbox(
    "Planet 2",
    sorted(df["planet_name"].dropna().unique()),
    key="p2"
)

col1, col2 = st.columns(2)

with col1:
    st.dataframe(
        df[df["planet_name"] == planet1]
    )

with col2:
    st.dataframe(
        df[df["planet_name"] == planet2]
    )
st.subheader("⭐ Star Comparison")

star1 = st.selectbox(
    "Star 1",
    sorted(df["star_name"].dropna().unique()),
    key="s1"
)

star2 = st.selectbox(
    "Star 2",
    sorted(df["star_name"].dropna().unique()),
    key="s2"
)

col1, col2 = st.columns(2)

with col1:
    st.dataframe(
        df[df["star_name"] == star1][
            [
                "star_name",
                "tempraure_k",
                "mass_solar",
                "radius_solar",
                "distance_ly"
            ]
        ].drop_duplicates()
    )

with col2:
    st.dataframe(
        df[df["star_name"] == star2][
            [
                "star_name",
                "tempraure_k",
                "mass_solar",
                "radius_solar",
                "distance_ly"
            ]
        ].drop_duplicates()
    )
st.subheader("🔥 Correlation Heatmap")

corr = df[
    [
        "planet_mass_earth",
        "planet_radius_earth",
        "equilibrium_temp_k",
        "distance_ly"
    ]
].corr()

fig = px.imshow(
    corr,
    text_auto=True,
    aspect="auto"
)

st.plotly_chart(fig, use_container_width=True)
st.divider()
st.divider()
st.divider()
st.subheader("🛰️ NASA Style Planetary System")

selected_star = st.selectbox(
    "Select Star System",
    sorted(df["star_name"].dropna().unique()),
    key="nasa_system"
)

system_df = df[df["star_name"] == selected_star]

fig = go.Figure()

# Star
fig.add_trace(
    go.Scatter(
        x=[0],
        y=[0],
        mode="markers",
        marker=dict(
            size=35,
            color="gold"
        ),
        name=selected_star
    )
)

for _, row in system_df.iterrows():

    orbit = row["semi_major_axis_au"]

    if pd.notnull(orbit):

        # Scale orbit
        scaled_orbit = max(float(orbit) * 25, 1)

        # Orbit Ring
        theta = np.linspace(0, 2*np.pi, 300)

        orbit_x = scaled_orbit * np.cos(theta)
        orbit_y = scaled_orbit * np.sin(theta)

        fig.add_trace(
            go.Scatter(
                x=orbit_x,
                y=orbit_y,
                mode="lines",
                line=dict(
                    color="rgba(255,255,255,0.25)",
                    width=1
                ),
                showlegend=False,
                hoverinfo="skip"
            )
        )

        # Planet position
        planet_x = scaled_orbit
        planet_y = 0

        # Planet size
        radius = row["planet_radius_earth"]

        if pd.isna(radius):
            size = 10
        else:
            size = max(min(float(radius) * 2, 40), 8)

        # Planet color
        ptype = str(row["planet_type"])

        if "Jupiter" in ptype:
            color = "orange"
        elif "Terrestrial" in ptype or "terrestrial" in ptype:
            color = "deepskyblue"
        elif "Super Earth" in ptype:
            color = "lime"
        elif "Neptune" in ptype:
            color = "cyan"
        elif "Lava" in ptype:
            color = "red"
        else:
            color = "white"

        # Hover values
        mass = row["planet_mass_earth"]
        temp = row["equilibrium_temp_k"]

        mass_text = "Unknown" if pd.isna(mass) else mass
        temp_text = "Unknown" if pd.isna(temp) else temp

        fig.add_trace(
            go.Scatter(
                x=[planet_x],
                y=[planet_y],
                mode="markers+text",
                text=[row["planet_name"]],
                textposition="top center",
                marker=dict(
                    size=size,
                    color=color,
                    line=dict(
                        color="white",
                        width=1
                    )
                ),
                name=row["planet_name"],
                hovertemplate=
                f"Planet: {row['planet_name']}<br>"
                f"Type: {row['planet_type']}<br>"
                f"Radius: {radius}<br>"
                f"Mass: {mass_text}<br>"
                f"Temperature: {temp_text} K<br>"
                f"Orbit: {orbit} AU"
            )
        )

fig.update_layout(
    height=800,
    title=f"{selected_star} System",
    paper_bgcolor="black",
    plot_bgcolor="black",
    font=dict(color="white"),
    xaxis=dict(
        visible=False
    ),
    yaxis=dict(
        visible=False,
        scaleanchor="x"
    ),
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)
st.write(system_df[["planet_name", "semi_major_axis_au"]])
