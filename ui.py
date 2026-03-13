import time
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
import folium
import json
import pydeck as pdk

from config import AIRPORT_COORDS
from radar import process_drones_for_ui, reset_radar_state

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Rogue Drone Radar",
    page_icon="🛡️",
    layout="wide"
)

from radar import process_drones_for_ui




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
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
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
        color: white;
    }
    .warning-box {
        padding: 12px;
        border-radius: 12px;
        background: rgba(214, 158, 46, 0.15);
        border-left: 6px solid #d69e2e;
        margin-bottom: 10px;
        color: white;
    }
    .clear-box {
        padding: 12px;
        border-radius: 12px;
        background: rgba(31, 157, 85, 0.15);
        border-left: 6px solid #1f9d55;
        margin-bottom: 10px;
        color: white;
    }
    [data-stale="true"] { opacity: 1 !important; filter: none !important; }
    div[data-testid="stStatusWidget"] { visibility: hidden; height: 0%; position: fixed; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data(ttl=10)
def get_drones():
    return process_drones_for_ui()

@st.cache_data
def load_zone_data():
    if os.path.exists('zone_restriction_uav.json'):
        with open('zone_restriction_uav.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_status_color(status):
    s = str(status).upper()
    if "CRITICAL" in s:
        return [229, 62, 62, 220]   # red
    if "WARNING" in s:
        return [214, 158, 46, 220]  # orange
    return [31, 157, 85, 220]       # green


def build_3d_map_df(drones):
    rows = []
    for d in drones:
        lat = d.get("Latitude")
        lng = d.get("Longitude")
        alt = d.get("Altitude AGL", 0)

        if lat is None or lng is None:
            continue

        try:
            altitude = float(alt) if alt is not None else 0
        except Exception:
            altitude = 0

        rows.append({
            "Drone ID": d["Drone ID"],
            "Pilot ID": d["Pilot ID"],
            "Status": d["Status"],
            "Latitude": float(lat),
            "Longitude": float(lng),
            "Altitude AGL": altitude,
            "Distance (m)": d["Distance (m)"],
            "Trend": d.get("Trend", ""),
            "color": get_status_color(d["Status"]),
            # make columns visible in 3D
            "elevation": max(altitude * 8, 30)
        })

    return pd.DataFrame(rows)

def build_zone_df(geo_data):
    zones = []

    for feature in geo_data["features"]:
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})

        if geom.get("type") != "Polygon":
            continue

        coords = geom.get("coordinates", [])
        if not coords:
            continue

        # GeoJSON stores coordinates as [lng, lat]
        polygon = [[c[0], c[1]] for c in coords[0]]

        zones.append({
            "polygon": polygon,
            "zone_id": props.get("zone_id", "Unknown"),
            "upper_lim": props.get("upper_lim", "Unknown"),
            "status": props.get("status", "")
        })

    return pd.DataFrame(zones)
def status_priority(status):
    s = str(status).upper()
    if "CRITICAL" in s: return 3
    if "WARNING" in s: return 2
    if "CLEAR" in s: return 1
    return 0

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("⚙️ Controls")
auto_refresh = st.sidebar.toggle("Auto refresh", value=True)
refresh_seconds = st.sidebar.slider("Refresh interval (sec)", 2, 30, 5)
show_raw = st.sidebar.toggle("Show raw JSON", value=False)
manual_refresh = st.sidebar.button("Refresh now")
pitch_angle = st.sidebar.slider("3D view angle", 0, 75, 55)
bearing_angle = st.sidebar.slider("Map rotation", -180, 180, 0)
zoom_level = st.sidebar.slider("Zoom level", 8.0, 16.0, 10.8, 0.1)

status_filter = st.sidebar.multiselect(
    "Filter live status",
    ["🔴 CRITICAL", "🟡 WARNING", "🟢 CLEAR"],
    default=[]
)

if manual_refresh:
    st.rerun()

# -----------------------------
# Header
# -----------------------------
st.title("🛡️ Rogue Drone Early Warning System")
st.caption("Live airport drone monitoring & historical audit platform")

# -----------------------------
# Load Data
# -----------------------------
try:
    drones = get_drones()
    drones = sorted(drones, key=lambda x: status_priority(x["Status"]), reverse=True)
except Exception as e:
    st.error(f"Could not load drone data: {e}")
    st.stop()

if status_filter:
    drones = [d for d in drones if d["Status"] in status_filter]

critical_count = sum(1 for d in drones if "CRITICAL" in d["Status"].upper())
warning_count = sum(1 for d in drones if "WARNING" in d["Status"].upper())
unknown_pilot_count = sum(1 for d in drones if d["Pilot ID"] == "Unknown")

# -----------------------------
# KPI Cards
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.markdown(f"<div class='metric-card'><div class='metric-title'>Total Drones</div><div class='metric-value'>{len(drones)}</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='metric-card'><div class='metric-title'>Critical</div><div class='metric-value' style='color:#e53e3e'>{critical_count}</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='metric-card'><div class='metric-title'>Warning</div><div class='metric-value' style='color:#d69e2e'>{warning_count}</div></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='metric-card'><div class='metric-title'>Unknown Pilot</div><div class='metric-value'>{unknown_pilot_count}</div></div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# Navigation Tabs
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
    st.subheader("🗺️ Live 3D Drone Map")

    airport_lat, airport_lng = AIRPORT_COORDS
    map_df = build_3d_map_df(drones)
    geo_data = load_zone_data()
    zone_df = build_zone_df(geo_data)
    if map_df.empty:
        st.info("No drone coordinates available for 3D map.")
    else:
        view_state = pdk.ViewState(
            latitude=airport_lat,
            longitude=airport_lng,
            zoom=zoom_level,
            pitch=pitch_angle,
            bearing=bearing_angle
        )

        drone_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position='[Longitude, Latitude]',
            get_radius=200,
            radius_scale=2,
            radius_min_pixels=6,
            radius_max_pixels=60,
            get_fill_color=[255, 0, 0, 240],  # brighter red
            get_line_color=[255, 255, 255],  # white outline
            line_width_min_pixels=2,
            pickable=True,
        )

        text_layer = pdk.Layer(
            "TextLayer",
            data=map_df,
            get_position='[Longitude, Latitude]',
            get_text="Drone ID",
            get_size=14,
            get_color=[20, 20, 20, 220],
            get_angle=0,
            get_text_anchor="'start'",
            get_alignment_baseline="'bottom'",
            pickable=False
        )

        airport_df = pd.DataFrame([{
            "name": "Airport",
            "Latitude": airport_lat,
            "Longitude": airport_lng
        }])

        airport_layer = pdk.Layer(
            "ScatterplotLayer",
            data=airport_df,
            get_position='[Longitude, Latitude]',
            get_radius=180,
            get_fill_color=[0, 140, 255, 200],
            pickable=True
        )

        tooltip = {
            "html": """
                    <b>ID:</b> {Drone ID}<br/>
                    <b>Pilot:</b> {Pilot ID}<br/>
                    <b>Status:</b> {Status}<br/>
                    <b>Altitude:</b> {Altitude AGL} m<br/>
                    <b>Distance:</b> {Distance (m)} m<br/>
                    <b>Trend:</b> {Trend}
                """,
            "style": {
                "backgroundColor": "rgba(20,20,20,0.85)",
                "color": "white"
            }
        }
        zone_layer = pdk.Layer(
            "PolygonLayer",
            data=zone_df,
            get_polygon="polygon",
            get_fill_color=[229, 62, 62, 80],
            get_line_color=[229, 62, 62, 200],
            line_width_min_pixels=2,
            pickable=True,
        )
        deck = pdk.Deck(
            map_style="light",
            initial_view_state=view_state,
            layers=[zone_layer,drone_layer, airport_layer, text_layer],
            tooltip=tooltip
        )

        st.pydeck_chart(deck, use_container_width=True)





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
tab_live, tab_archive = st.tabs(["📡 Live Radar", "📂 Flight Archive"])

with tab_live:
    left, right = st.columns([1, 1.35])

    with left:
        st.subheader("🚨 Active Alerts")
        shown_any = False
        for d in drones[:8]:
            status = d["Status"].upper()
            if "CRITICAL" in status:
                st.markdown(f"<div class='critical-box'><b>{d['Drone ID']}</b><br>Pilot: {d['Pilot ID']}<br>Distance: {d['Distance (m)']} m<br>{d['Reasons']}</div>", unsafe_allow_html=True)
                shown_any = True
            elif "WARNING" in status:
                st.markdown(f"<div class='warning-box'><b>{d['Drone ID']}</b><br>Pilot: {d['Pilot ID']}<br>Distance: {d['Distance (m)']} m<br>{d['Reasons']}</div>", unsafe_allow_html=True)
                shown_any = True

        if not shown_any:
            st.markdown("<div class='clear-box'><b>No active dangerous alerts.</b></div>", unsafe_allow_html=True)

    with right:
        st.subheader("🗺️ Live Drone Map")
        airport_lat, airport_lng = AIRPORT_COORDS
        m = folium.Map(location=[airport_lat, airport_lng], zoom_start=11, tiles="CartoDB positron")

        geo_data = load_zone_data()
        if geo_data:
            folium.GeoJson(
                geo_data,
                name="Restricted Airspace",
                style_function=lambda x: {'fillColor': '#e53e3e', 'color': '#e53e3e', 'weight': 1, 'fillOpacity': 0.15},
                tooltip=folium.GeoJsonTooltip(fields=['zone_id', 'upper_lim', 'status'], aliases=['Zone ID:', 'Max Alt:', 'Status:'])
            ).add_to(m)

        for d in drones:
            lat, lng = d["Latitude"], d["Longitude"]
            if lat is None or lng is None: continue
            status = d["Status"].upper()
            main_color = "red" if "CRITICAL" in status else "orange" if "WARNING" in status else "green"

            history_points = d.get("raw", {}).get("history", [])
            if history_points:
                path_coords = [[p['lat'], p['lng']] for p in history_points]
                path_coords.append([lat, lng])
                folium.PolyLine(locations=path_coords, color=main_color, weight=2, opacity=0.4, dash_array='5, 10').add_to(m)

            popup_html = f'<div style="font-family: sans-serif; width: 150px;"><b style="color:{main_color}">{d["Drone ID"]}</b><br><b>Alt:</b> {d["Altitude AGL"]}m<br><b>Trend:</b> {d["Trend"]}</div>'
            folium.CircleMarker(location=[lat, lng], radius=8, color=main_color, fill=True, fill_color=main_color, fill_opacity=1.0, popup=folium.Popup(popup_html, max_width=200), tooltip=f"LIVE: {d['Drone ID']}").add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, width=None, height=520, key="live_map")

    st.subheader("📋 Live Drone Feed")
    if drones:
        df_display = pd.DataFrame(drones).drop(columns=['raw'])
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No active drones detected.")

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
                st.write(f"**Altitude AGL:** {d['Altitude AGL']} m")
            with c:
                st.write(f"**Heading:** {d['Heading (°)']}°")
                st.write(f"**Lat:** {d['Latitude']}")
                st.write(f"**Lng:** {d['Longitude']}")
                st.write(f"**Reasons:** {d['Reasons']}")
            if show_raw:
                with st.expander("Raw drone JSON"):
                    st.json(d["raw"])

with tab_archive:
    st.header("📂 Historical Incident Archive")
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        archive_window = st.selectbox("Time Window", ["All Records", "Last Hour", "Last 24 Hours", "Last 7 Days"])
    with col_f2:
        st.write("")
        if st.button("🗑️ Clear All History", type="secondary", help="Deletes the local CSV and resets logs"):
            if os.path.exists('drone_incidents.csv'):
                os.remove('drone_incidents.csv')
                reset_radar_state()
                st.success("History file deleted successfully.")
                time.sleep(1)
                st.rerun()
            else:
                st.info("No history file to delete.")

    if os.path.exists('drone_incidents.csv'):
        try:
            hist_df = pd.read_csv('drone_incidents.csv', on_bad_lines='warn')
            if not hist_df.empty:
                st.dataframe(hist_df.sort_values(by=['Date', 'Timestamp'], ascending=False), use_container_width=True, hide_index=True)
                csv = hist_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="📥 Download Flight Logs (CSV)", data=csv, file_name="flight_audit_logs.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Archive corrupted: {e}")
            if st.button("Reset Archive File"):
                os.remove('drone_incidents.csv')
                st.rerun()

if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="radar_refresh_global")