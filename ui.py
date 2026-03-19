import os
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pydeck as pdk
from config import ROMANIA_CENTER_LAT, ROMANIA_CENTER_LNG
from radar import process_drones_for_ui, reset_radar_state, status_priority
from airspace_manager import build_zone_df
from risk_calculator import airspace
from utils import get_status_color

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Rogue Drone Radar",
    page_icon="🛡️",
    layout="wide"
)

# -----------------------------
# Styling (The "Tactical Console" Look)
# -----------------------------
st.markdown("""
<style>
    .main { background: linear-gradient(180deg, #081221 0%, #0d1728 100%); }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .metric-card {
        border-radius: 16px; padding: 16px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .metric-title { font-size: 0.9rem; color: #a0aec0; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: white; }
    .critical-box {
        padding: 12px; border-radius: 12px;
        background: rgba(229, 62, 62, 0.15);
        border-left: 6px solid #e53e3e;
        margin-bottom: 10px; color: white;
    }
    .warning-box {
        padding: 12px; border-radius: 12px;
        background: rgba(214, 158, 46, 0.15);
        border-left: 6px solid #d69e2e;
        margin-bottom: 10px; color: white;
    }
    .clear-box {
        padding: 12px; border-radius: 12px;
        background: rgba(31, 157, 85, 0.15);
        border-left: 6px solid #1f9d55;
        margin-bottom: 10px; color: white;
    }
    div[data-testid="stStatusWidget"] { visibility: hidden; height: 0%; position: fixed; }
    [data-stale="true"] { opacity: 1 !important; filter: none !important; }
    div[data-testid="stStatusWidget"] { visibility: hidden; height: 0%; position: fixed; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.title("⚙️ Radar Controls")
auto_refresh = st.sidebar.toggle("Auto refresh", value=True)
refresh_seconds = st.sidebar.slider("Refresh interval (sec)", 2, 30, 5)
show_raw = st.sidebar.toggle("Show raw JSON", value=False)
pitch_angle = st.sidebar.slider("3D view angle", 0, 60, 45)  # Capped at 60 to prevent blackouts

if st.sidebar.button("Force Refresh Now"):
    st.rerun()

# -----------------------------
# Data Processing
# -----------------------------
try:
    drones = process_drones_for_ui()
    drones = sorted(drones, key=lambda x: status_priority(x["Status"]), reverse=True)
except Exception as e:
    st.error(f"Radar Engine Error: {e}")
    st.stop()

# -----------------------------
# Header & KPI Section
# -----------------------------
st.title("🛡️ Rogue Drone Early Warning System")
st.caption("National Airspace Monitoring | Real-time 3D Intrusion Detection")

crit_count = sum(1 for d in drones if "CRITICAL" in d["Status"].upper())
warn_count = sum(1 for d in drones if "WARNING" in d["Status"].upper())

c1, c2, c3, c4 = st.columns(4)
c1.markdown(
    f"<div class='metric-card'><div class='metric-title'>Active Drones</div><div class='metric-value'>{len(drones)}</div></div>",
    unsafe_allow_html=True)
c2.markdown(
    f"<div class='metric-card'><div class='metric-title'>Critical Threats</div><div class='metric-value' style='color:#e53e3e'>{crit_count}</div></div>",
    unsafe_allow_html=True)
c3.markdown(
    f"<div class='metric-card'><div class='metric-title'>Warnings</div><div class='metric-value' style='color:#d69e2e'>{warn_count}</div></div>",
    unsafe_allow_html=True)
c4.markdown(
    f"<div class='metric-card'><div class='metric-title'>Sector Status</div><div class='metric-value'>ACTIVE</div></div>",
    unsafe_allow_html=True)

st.write("")

# -----------------------------
# Main Navigation
# -----------------------------
tab_live, tab_archive = st.tabs(["📡 Live Radar", "📂 Flight Archive"])

with tab_live:
    left, right = st.columns([1, 1.35])

    with left:
        st.subheader("🚨 Priority Alerts")
        shown_any = False
        for d in drones[:8]:
            status = d["Status"].upper()
            if "CRITICAL" in status:
                st.markdown(f"<div class='critical-box'><b>{d['Drone ID']}</b><br>{d['Reasons']}</div>",
                            unsafe_allow_html=True)
                shown_any = True
            elif "WARNING" in status:
                st.markdown(f"<div class='warning-box'><b>{d['Drone ID']}</b><br>{d['Reasons']}</div>",
                            unsafe_allow_html=True)
                shown_any = True

        if not shown_any:
            st.markdown("<div class='clear-box'><b>No active threats in sector.</b></div>", unsafe_allow_html=True)

    with right:
        st.subheader("🗺️ Tactical 3D Map")

        # Prepare Map Data using reorganized helper functions
        map_df = pd.DataFrame(drones)
        zone_df = build_zone_df(airspace)  # Uses the pre-loaded instance

        view_state = pdk.ViewState(
            latitude=ROMANIA_CENTER_LAT,
            longitude=ROMANIA_CENTER_LNG,
            zoom=5.7,
            pitch=pitch_angle,
            bearing=0
        )

        # Get path of drones
        path_data = []
        for d in drones:
            history = d.get("raw", {}).get("history", [])
            if history:
                coords = [[p['lng'], p['lat']] for p in history]
                coords.append([d['Longitude'], d['Latitude']])
                path_data.append({
                    "path": coords,
                    "color": get_status_color(d["Status"])
                })

        # Zones, drones layers
        layers = [
            pdk.Layer("PathLayer", data=path_data, get_path="path", get_color="color", width_min_pixels=2,
                      dash_array=[5, 5], cap_rounded=True),
            pdk.Layer(
                "LineLayer",
                data=map_df,
                get_source_position="[Longitude, Latitude]",
                get_target_position="[Future_Lng, Future_Lat]",
                get_color="color",
                get_width=3
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[Longitude, Latitude]',
                get_fill_color="color",
                get_radius=800,
                radius_min_pixels=15,
                radius_max_pixels=30,
                opacity=0.4,
                pickable=False,
            ),
            pdk.Layer(
                "ColumnLayer",
                data=map_df,
                get_position='[Longitude, Latitude]',
                get_elevation='elevation',
                # FIX 3: Increased scale for better 3D definition at limited pitch
                elevation_scale=1,
                radius=15,
                radius_units="'meters'",
                radius_min_pixels=4,
                radius_max_pixels=12,
                get_fill_color="color",
                pickable=True,
                extruded=True,
                coverage=1
            ),
            pdk.Layer("PolygonLayer", data=zone_df, get_polygon="polygon", get_fill_color=[229, 62, 62, 80],
                      get_line_color=[229, 62, 62, 200],
                      line_width_min_pixels=2, pickable=True, extruded=True, get_elevation="elevation",
                      elevation_scale=1, )
        ]

        # Text box with info
        tooltip = {
            "html": """
                            <div style='font-family: sans-serif;'>
                                # IF DRONE
                                <div style='display: {["Drone ID"] ? "block" : "none"}'>
                                    <b>Drone ID:</b> {Drone ID}<br/>
                                    <b>Status:</b> {Status}<br/>
                                    <b>Altitude:</b> {Altitude AGL} m
                                </div>

                                # IF ZONE
                                <div style='display: {zone_id ? "block" : "none"}'>
                                    <b>Zone:</b> {zone_id}<br/>
                                    <b>Min Alt:</b> {min_alt}<br/>
                                    <b>Max Alt:</b> {max_alt}<br/>
                                    <b>Status:</b> {status}
                                </div>
                            </div>
                        """,
            "style": {
                "backgroundColor": "rgba(20,20,20,0.9)",
                "color": "white",
                "borderRadius": "8px",
                "padding": "10px"
            }
        }

        # Apply to the deck
        st.pydeck_chart(
            pdk.Deck(
                map_style="light",
                initial_view_state=view_state,
                layers=layers,
                tooltip=tooltip
            ),
            use_container_width=True,
            key="radar_map_primary"
        )

    st.subheader("📋 Operations Log")
    if drones:
        df_display = pd.DataFrame(drones).drop(columns=['raw'])
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# -----------------------------
# Archive Logic
# -----------------------------
with tab_archive:
    st.header("📂 Flight Incident Logs")
    if os.path.exists('drone_incidents.csv'):
        hist_df = pd.read_csv('drone_incidents.csv')
        st.dataframe(hist_df.sort_values(by=['Date', 'Timestamp'], ascending=False), use_container_width=True)

        if st.button("Clear Logs"):
            os.remove('drone_incidents.csv')
            reset_radar_state()
            st.rerun()
    else:
        st.info("No recorded incidents.")

# -----------------------------
# Auto-Refresh Logic
# -----------------------------
if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="ui_refresh_timer")