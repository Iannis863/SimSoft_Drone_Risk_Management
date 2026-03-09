import time
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

from config import AIRPORT_COORDS

st.set_page_config(
    page_title="Rogue Drone Radar",
    page_icon="🛡️",
    layout="wide"
)

from radar import process_drones_for_ui
from risk_calculator import assess_risk, get_heading



# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
    .main {
        background: linear-gradient(180deg, #081221 0%, #0d1728 100%);
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .metric-card {
        border-radius: 16px;
        padding: 16px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .metric-title {
        font-size: 0.9rem;
        color: #a0aec0;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: white;
    }
    .critical-box {
        padding: 12px;
        border-radius: 12px;
        background: rgba(229, 62, 62, 0.15);
        border-left: 6px solid #e53e3e;
        margin-bottom: 10px;
    }
    .warning-box {
        padding: 12px;
        border-radius: 12px;
        background: rgba(214, 158, 46, 0.15);
        border-left: 6px solid #d69e2e;
        margin-bottom: 10px;
    }
    .clear-box {
        padding: 12px;
        border-radius: 12px;
        background: rgba(31, 157, 85, 0.15);
        border-left: 6px solid #1f9d55;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helpers
# -----------------------------






def status_priority(status):
    s = str(status).upper()
    if "CRITICAL" in s:
        return 3
    if "WARNING" in s:
        return 2
    if "CLEAR" in s:
        return 1
    return 0


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("⚙️ Controls")
auto_refresh = st.sidebar.toggle("Auto refresh", value=True)
refresh_seconds = st.sidebar.slider("Refresh interval (sec)", 2, 15, 2)
show_raw = st.sidebar.toggle("Show raw JSON", value=False)
manual_refresh = st.sidebar.button("Refresh now")

status_filter = st.sidebar.multiselect(
    "Filter status",
    ["🔴 CRITICAL", "🟡 WARNING", "🟢 CLEAR"],
    default=[]
)

if manual_refresh:
    st.rerun()

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()

# -----------------------------
# Header
# -----------------------------
st.title("🛡️ Rogue Drone Early Warning System")
st.caption("Live airport drone monitoring dashboard powered by FLUX sensor data")

# -----------------------------
# Load Data
# -----------------------------
try:
    drones = process_drones_for_ui()
    drones = sorted(drones, key=lambda x: status_priority(x["Status"]), reverse=True)
except Exception as e:
    st.error(f"Could not load drone data from radar.py: {e}")
    st.stop()

if status_filter:
    drones = [d for d in drones if d["Status"] in status_filter]

critical_count = sum(1 for d in drones if "CRITICAL" in d["Status"].upper())
warning_count = sum(1 for d in drones if "WARNING" in d["Status"].upper())
clear_count = sum(1 for d in drones if "CLEAR" in d["Status"].upper())
unknown_pilot_count = sum(1 for d in drones if d["Pilot ID"] == "Unknown")

# -----------------------------
# KPI Cards
# -----------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"<div class='metric-card'><div class='metric-title'>Total Drones</div><div class='metric-value'>{len(drones)}</div></div>",
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"<div class='metric-card'><div class='metric-title'>Critical</div><div class='metric-value'>{critical_count}</div></div>",
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"<div class='metric-card'><div class='metric-title'>Warning</div><div class='metric-value'>{warning_count}</div></div>",
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f"<div class='metric-card'><div class='metric-title'>Unknown Pilot</div><div class='metric-value'>{unknown_pilot_count}</div></div>",
        unsafe_allow_html=True
    )

st.write("")

# -----------------------------
# Alerts + Map
# -----------------------------
left, right = st.columns([1, 1.35])

with left:
    st.subheader("🚨 Active Alerts")

    shown_any = False
    for d in drones[:8]:
        status = d["Status"].upper()
        if "CRITICAL" in status:
            st.markdown(
                f"<div class='critical-box'><b>{d['Drone ID']}</b><br>"
                f"Pilot: {d['Pilot ID']}<br>"
                f"Distance: {d['Distance (m)']} m<br>"
                f"{d['Reasons']}</div>",
                unsafe_allow_html=True
            )
            shown_any = True
        elif "WARNING" in status:
            st.markdown(
                f"<div class='warning-box'><b>{d['Drone ID']}</b><br>"
                f"Pilot: {d['Pilot ID']}<br>"
                f"Distance: {d['Distance (m)']} m<br>"
                f"{d['Reasons']}</div>",
                unsafe_allow_html=True
            )
            shown_any = True

    if not shown_any:
        st.markdown(
            "<div class='clear-box'><b>No active dangerous alerts.</b></div>",
            unsafe_allow_html=True
        )

with right:
    st.subheader("🗺️ Live Drone Map")


    airport_lat, airport_lng = AIRPORT_COORDS

    m = folium.Map(
        location=[airport_lat, airport_lng],
        zoom_start=11,
        tiles="CartoDB positron"
    )

    # Airport marker
    folium.Marker(
        [airport_lat, airport_lng],
        tooltip="Henri Coandă Airport"
    ).add_to(m)

    # Danger zone
    folium.Circle(
        location=[airport_lat, airport_lng],
        radius=1500,
        color="red",
        fill=True,
        fill_opacity=0.08,
        tooltip="Airport Danger Zone"
    ).add_to(m)

    # Drone markers
    for d in drones:
        lat = d["Latitude"]
        lng = d["Longitude"]

        if lat is None or lng is None:
            continue

        status = d["Status"].upper()

        if "CRITICAL" in status:
            color = "red"
        elif "WARNING" in status:
            color = "orange"
        else:
            color = "green"

        popup_html = f"""
            <b>Drone:</b> {d['Drone ID']}<br>
            <b>Pilot:</b> {d['Pilot ID']}<br>
            <b>Status:</b> {d['Status']}<br>
            <b>Distance:</b> {d['Distance (m)']} m<br>
            <b>Altitude:</b> {d['Altitude AGL']}<br>
            <b>Heading:</b> {d['Heading (°)']}°
            """

        folium.CircleMarker(
            location=[lat, lng],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=popup_html,
            tooltip=d["Drone ID"]
        ).add_to(m)

    st_folium(m, width="100%", height=520)

# -----------------------------
# Table
# -----------------------------
st.write("")
st.subheader("📋 Live Drone Feed")

if drones:
    df = pd.DataFrame([{
        "Drone ID": d["Drone ID"],
        "Pilot ID": d["Pilot ID"],
        "Status": d["Status"],
        "Risk Score": d["Risk Score"],
        "Distance (m)": d["Distance (m)"],
        "Heading (°)": d["Heading (°)"],
        "Altitude AGL": d["Altitude AGL"],
        "Latitude": d["Latitude"],
        "Longitude": d["Longitude"],
        "Reasons": d["Reasons"]
    } for d in drones])

    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No drones found.")

# -----------------------------
# Detailed Cards
# -----------------------------
st.write("")
st.subheader("🔎 Detailed Drone Cards")

for d in drones[:12]:
    with st.container(border=True):
        a, b, c = st.columns(3)

        with a:
            st.markdown(f"### {d['Drone ID']}")
            st.write(f"**Pilot ID:** {d['Pilot ID']}")
            st.write(f"**Status:** {d['Status']}")

        with b:
            st.write(f"**Risk Score:** {d['Risk Score']}")
            st.write(f"**Distance:** {d['Distance (m)']} m")
            st.write(f"**Altitude AGL:** {d['Altitude AGL']}")

        with c:
            st.write(f"**Heading:** {d['Heading (°)']}°")
            st.write(f"**Lat:** {d['Latitude']}")
            st.write(f"**Lng:** {d['Longitude']}")
            st.write(f"**Reasons:** {d['Reasons']}")

        if show_raw:
            with st.expander("Raw drone JSON"):
                st.json(d["raw"])