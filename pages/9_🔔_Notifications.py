import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.helpers import require_login, time_ago, get_media_path, post_card_css

st.set_page_config(page_title="Notifications · Dzone", page_icon="🔔", layout="wide")
st.markdown(post_card_css(), unsafe_allow_html=True)

user = require_login()

col_header, col_btn = st.columns([4, 1])
with col_header:
    st.markdown("# 🔔 Notifications")
with col_btn:
    if st.button("✅ Mark all read"):
        db.mark_notifications_read(user["id"])
        st.rerun()

notifs = db.get_notifications(user["id"])

if not notifs:
    st.info("No notifications yet.")
else:
    ICONS = {
        "like":    "❤️",
        "comment": "💬",
        "follow":  "👤",
        "zone":    "📡",
        "mention": "🔔",
    }
    for n in notifs:
        icon = ICONS.get(n.get("type",""), "🔔")
        bg = "#1F1F1F" if n.get("is_read") else "#2A1A1A"
        dot = "" if n.get("is_read") else ' <span style="color:#FF2D55; font-size:10px;">● NEW</span>'

        with st.container():
            st.markdown(
                f'<div style="background:{bg}; border-radius:10px; padding:12px 16px; '
                f'margin-bottom:8px; border:1px solid #333;">',
                unsafe_allow_html=True
            )
            c1, c2 = st.columns([1, 8])
            with c1:
                av = get_media_path(n.get("avatar_path"))
                if av:
                    st.image(av, width=40)
                else:
                    st.markdown(icon)
            with c2:
                from_name = f"@{n['username']}" if n.get("username") else "Someone"
                st.markdown(
                    f"**{from_name}** {n['content']}{dot}",
                    unsafe_allow_html=True
                )
                st.caption(time_ago(n["created_at"]))
                if n.get("post_id"):
                    st.page_link("pages/1_🏠_Feed.py", label="View post →")
                if n.get("zone_id"):
                    st.page_link("pages/6_📡_Zone.py", label="Go to Zone →")
            st.markdown('</div>', unsafe_allow_html=True)
