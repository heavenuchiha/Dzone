import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.helpers import require_login, format_count, time_ago, get_media_path, post_card_css, haversine
from datetime import datetime
import time

st.set_page_config(page_title="Zone · Dzone", page_icon="📡", layout="wide")
st.markdown(post_card_css(), unsafe_allow_html=True)
st.markdown("""
<style>
.zone-active { border: 2px solid #FF2D55 !important; }
.zone-ended  { border: 2px solid #444 !important; opacity: 0.7; }
.chat-bubble-me {
    background: #FF2D55; color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 8px 14px; margin: 4px 0; max-width: 70%;
    margin-left: auto; text-align: right;
}
.chat-bubble-other {
    background: #2A2A2A; color: white;
    border-radius: 18px 18px 18px 4px;
    padding: 8px 14px; margin: 4px 0; max-width: 70%;
}
.chat-bubble-system {
    background: transparent; color: #888;
    text-align: center; font-size: 12px;
    padding: 4px; margin: 4px auto;
}
</style>
""", unsafe_allow_html=True)

user = require_login()

# auto-expire inactive zones
db.check_zone_inactivity()

st.markdown("# 📡 Zone")
st.caption("Broadcast to people within 1–5 km · First 10 to accept join your chat")

# ── Location ──────────────────────────────────────────────────────────────────
st.markdown("### 📍 Your Location")
st.info("Zone uses your GPS location to find nearby users. Enter your coordinates manually or allow location access below.")

try:
    from streamlit_js_eval import get_geolocation
    loc = get_geolocation()
    if loc and loc.get("coords"):
        lat = loc["coords"]["latitude"]
        lon = loc["coords"]["longitude"]
        st.session_state.user_lat = lat
        st.session_state.user_lon = lon
        st.success(f"📍 Location detected: {lat:.4f}, {lon:.4f}")
    else:
        raise Exception("No coords")
except Exception:
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input("Latitude", value=st.session_state.get("user_lat", 18.0179),
                               format="%.6f", key="lat_input")
    with col_lon:
        lon = st.number_input("Longitude", value=st.session_state.get("user_lon", -76.8099),
                               format="%.6f", key="lon_input")
    st.session_state.user_lat = lat
    st.session_state.user_lon = lon

user_lat = st.session_state.get("user_lat", 18.0179)
user_lon = st.session_state.get("user_lon", -76.8099)

st.divider()

tab_browse, tab_create, tab_my_zone = st.tabs(["🔍 Nearby Zones", "📡 Create Zone", "💬 My Zone"])

# ── Browse nearby zones ───────────────────────────────────────────────────────
with tab_browse:
    search_radius = st.slider("Search radius (km)", 1, 50, 20)
    nearby = db.get_nearby_zones(user_lat, user_lon, radius_km=search_radius)

    # filter by actual haversine distance and zone radius
    valid_zones = []
    for z in nearby:
        dist = haversine(user_lat, user_lon, z["latitude"], z["longitude"])
        if dist <= max(search_radius, z.get("radius_km", 3)):
            z["_distance_km"] = round(dist, 2)
            valid_zones.append(z)

    valid_zones.sort(key=lambda x: x["_distance_km"])

    if not valid_zones:
        st.info(f"No active zones within {search_radius} km. Be the first to create one!")
    else:
        st.caption(f"{len(valid_zones)} active zone(s) nearby")

    for z in valid_zones:
        is_active = z["status"] == "active"
        is_member = db.is_zone_member(z["id"], user["id"])
        card_class = "zone-active" if is_active else "zone-ended"

        with st.container():
            st.markdown(f'<div class="zone-card {card_class}">', unsafe_allow_html=True)
            c1, c2 = st.columns([3, 1])
            with c1:
                status_dot = "🟢" if is_active else "🔴"
                st.markdown(f"### {status_dot} {z['title']}")
                st.caption(f"by @{z['username']}  ·  📍 {z['_distance_km']} km away  ·  👥 {z['member_count']}/10 members")
                if z.get("description"):
                    st.markdown(z["description"])
                st.caption(f"⏱️ Created {time_ago(z['created_at'])}")
                if z.get("rating_count", 0) > 0:
                    stars = "⭐" * round(z.get("rating_avg", 0))
                    st.caption(f"{stars} {z['rating_avg']:.1f} ({z['rating_count']} ratings)")
            with c2:
                if is_member:
                    st.success("✅ Member")
                    if st.button("Enter Zone", key=f"enter_{z['id']}", use_container_width=True):
                        st.session_state.active_zone_id = z["id"]
                        st.rerun()
                elif is_active and int(z.get("member_count", 0)) < 10:
                    if st.button("📡 Join Zone", key=f"join_{z['id']}", use_container_width=True, type="primary"):
                        ok, msg = db.request_join_zone(z["id"], user["id"])
                        if ok:
                            st.session_state.active_zone_id = z["id"]
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                elif int(z.get("member_count", 0)) >= 10:
                    st.warning("Zone Full")
                else:
                    st.info("Zone Ended")
            st.markdown('</div>', unsafe_allow_html=True)

# ── Create Zone ───────────────────────────────────────────────────────────────
with tab_create:
    st.markdown("### 📡 Broadcast a New Zone")
    st.info(
        "A Zone is a local broadcast chat. Enter a topic, set your radius (1–5 km), "
        "and the first 10 people in range who join will be added. "
        "The zone closes after **10 minutes of inactivity** or when you end it."
    )

    z_title = st.text_input("Zone Title / Topic", placeholder="e.g. 'Need directions downtown' or 'Looking for a gym buddy'")
    z_desc = st.text_area("Description (optional)", placeholder="Add more details about your zone…", height=80)
    z_radius = st.slider("Broadcast Radius (km)", min_value=1, max_value=5, value=3,
                          help="Only users within this distance will see your zone")

    col_info = st.columns(3)
    col_info[0].metric("Your Location", f"{user_lat:.4f}, {user_lon:.4f}")
    col_info[1].metric("Radius", f"{z_radius} km")
    col_info[2].metric("Max Members", "10")

    if st.button("📡 Launch Zone", type="primary", use_container_width=True):
        if not z_title.strip():
            st.error("Please enter a zone title.")
        else:
            zone_id = db.create_zone(user["id"], z_title.strip(), z_desc.strip(), user_lat, user_lon, z_radius)
            st.session_state.active_zone_id = zone_id
            st.success(f"Zone '{z_title}' is live! Share it and wait for people to join.")
            st.rerun()

# ── My Zone (active chat) ─────────────────────────────────────────────────────
with tab_my_zone:
    active_zone_id = st.session_state.get("active_zone_id")

    if not active_zone_id:
        st.info("You're not in an active zone. Join or create one above.")
    else:
        z = db.get_zone(active_zone_id)
        if not z:
            st.error("Zone not found.")
            st.session_state.active_zone_id = None
        else:
            is_creator = z["creator_id"] == user["id"]
            is_member  = db.is_zone_member(z["id"], user["id"])
            is_active  = z["status"] == "active"

            # header
            status_text = "🟢 Active" if is_active else "🔴 Ended"
            st.markdown(f"### 📡 {z['title']}")
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("Status", status_text)
            col_s2.metric("Members", f"{z['member_count']}/10")
            col_s3.metric("Creator", f"@{z['username']}")
            if not is_active and z.get("ended_at"):
                st.caption(f"Ended: {time_ago(z['ended_at'])}")

            # members list
            with st.expander("👥 Zone Members"):
                members = db.get_zone_members(z["id"])
                for m in members:
                    av = get_media_path(m.get("avatar_path"))
                    c1, c2 = st.columns([1, 6])
                    with c1:
                        if av:
                            st.image(av, width=32)
                        else:
                            st.markdown("👤")
                    with c2:
                        crown = "👑 " if m["id"] == z["creator_id"] else ""
                        st.markdown(f"{crown}**@{m['username']}**")
                        st.caption(f"Joined {time_ago(m['joined_at'])}")

            # chat messages
            st.markdown("#### 💬 Chat")
            messages = db.get_zone_messages(z["id"])
            chat_container = st.container(height=400)
            with chat_container:
                for msg in messages:
                    mtype = msg.get("message_type", "text")
                    if mtype == "system":
                        st.markdown(
                            f'<div class="chat-bubble-system">ℹ️ {msg["content"]}</div>',
                            unsafe_allow_html=True
                        )
                    elif msg["user_id"] == user["id"]:
                        st.markdown(
                            f'<div style="display:flex; justify-content:flex-end;">'
                            f'<div class="chat-bubble-me">'
                            f'<div style="font-size:11px;opacity:.7;">{time_ago(msg["created_at"])}</div>'
                            f'{msg["content"]}'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f'<div class="chat-bubble-other">'
                            f'<div style="font-size:11px;color:#FF2D55;">@{msg["username"]}</div>'
                            f'{msg["content"]}'
                            f'<div style="font-size:11px;opacity:.5;">{time_ago(msg["created_at"])}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

            if is_active and is_member:
                new_msg = st.text_input("Message…", key="zone_msg_input", placeholder="Type your message here…")
                col_send, col_refresh, col_end = st.columns([3, 1, 1])
                with col_send:
                    if st.button("Send ➤", type="primary", use_container_width=True):
                        if new_msg.strip():
                            db.send_zone_message(z["id"], user["id"], new_msg.strip())
                            st.rerun()
                with col_refresh:
                    if st.button("🔄 Refresh"):
                        st.rerun()
                with col_end:
                    if is_creator:
                        if st.button("🛑 End Zone", type="secondary"):
                            db.end_zone(z["id"], user["id"])
                            st.session_state.active_zone_id = None
                            st.rerun()

            # rating after zone ends
            if not is_active and is_member and not is_creator:
                st.divider()
                st.markdown("#### ⭐ Rate this Zone")
                rating_val = st.slider("How helpful was this zone?", 1, 5, 3, key="zone_rating")
                if st.button("Submit Rating"):
                    db.rate_zone(z["id"], user["id"], rating_val)
                    st.success("Thanks for your rating!")

            if not is_active:
                if st.button("Leave Zone View"):
                    st.session_state.active_zone_id = None
                    st.rerun()
