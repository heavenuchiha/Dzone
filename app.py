import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import database as db
from utils.helpers import get_country_list, get_country_code, post_card_css

st.set_page_config(
    page_title="Dzone",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

db.init_db()

st.markdown(post_card_css(), unsafe_allow_html=True)
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #111111; }
.dzone-logo { font-size: 2.5rem; font-weight: 900; color: #FF2D55; letter-spacing: -1px; }
.dzone-tagline { color: #888; font-size: 1rem; margin-top: -10px; }
.auth-box { max-width: 420px; margin: auto; padding: 32px; background: #1A1A1A;
            border-radius: 16px; border: 1px solid #2A2A2A; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar nav ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="dzone-logo">📡 Dzone</div>', unsafe_allow_html=True)
    st.markdown('<div class="dzone-tagline">Connect. Create. Zone In.</div>', unsafe_allow_html=True)
    st.divider()

    if "user" in st.session_state and st.session_state.user:
        user = st.session_state.user
        unread = db.get_unread_notification_count(user["id"])
        st.markdown(f"**👤 {user['display_name'] or user['username']}**")
        st.caption(f"@{user['username']} · {user['country']}")
        st.divider()
        st.page_link("pages/1_🏠_Feed.py",          label="🏠  For You")
        st.page_link("pages/2_🌍_Explore.py",        label="🌍  Explore")
        st.page_link("pages/3_🗺️_Country_Feed.py",   label="🗺️  My Country")
        st.page_link("pages/4_🌐_Global_Feed.py",    label="🌐  Global")
        st.page_link("pages/5_🏆_Top_Zone.py",       label="🏆  Top Zone")
        st.page_link("pages/6_📡_Zone.py",           label="📡  Zone")
        st.page_link("pages/7_📤_Upload.py",         label="📤  Upload")
        st.page_link("pages/8_👤_Profile.py",        label="👤  Profile")
        notif_label = f"🔔  Notifications{'  🔴' if unread > 0 else ''}"
        st.page_link("pages/9_🔔_Notifications.py",  label=notif_label)
        st.page_link("pages/10_💬_Messages.py",      label="💬  Messages")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    else:
        st.info("Log in or sign up to get started.")

# ── Main content ─────────────────────────────────────────────────────────────
if "user" in st.session_state and st.session_state.user:
    st.markdown("## Welcome back! 👋")
    st.markdown("Use the sidebar to navigate Dzone.")
    cols = st.columns(4)
    with cols[0]:
        st.page_link("pages/1_🏠_Feed.py", label="🏠 For You Feed", use_container_width=True)
    with cols[1]:
        st.page_link("pages/6_📡_Zone.py", label="📡 Open a Zone", use_container_width=True)
    with cols[2]:
        st.page_link("pages/5_🏆_Top_Zone.py", label="🏆 Top Zone", use_container_width=True)
    with cols[3]:
        st.page_link("pages/7_📤_Upload.py", label="📤 Post Content", use_container_width=True)
else:
    # landing / auth page
    col_l, col_r = st.columns([1, 1], gap="large")

    with col_l:
        st.markdown("""
        <div style="padding: 48px 24px;">
            <div style="font-size:3.5rem; font-weight:900; color:#FF2D55; line-height:1;">📡 Dzone</div>
            <div style="font-size:1.4rem; color:#fff; margin-top:12px; font-weight:600;">
                Connect. Create. Zone In.
            </div>
            <div style="color:#888; margin-top:16px; font-size:1rem; line-height:1.6;">
                Share videos & photos · Explore your country & the world<br>
                Compete in monthly <b style="color:#FFD700;">Top Zone</b> rankings<br>
                Connect locally with the <b style="color:#FF2D55;">Zone</b> broadcast feature
            </div>
            <div style="margin-top:32px; display:flex; gap:12px; flex-wrap:wrap;">
                <span style="background:#FF2D5520; color:#FF2D55; padding:8px 16px; border-radius:20px;">🎬 Videos & Photos</span>
                <span style="background:#FF2D5520; color:#FF2D55; padding:8px 16px; border-radius:20px;">🗺️ Country Feed</span>
                <span style="background:#FF2D5520; color:#FF2D55; padding:8px 16px; border-radius:20px;">🌐 Global Feed</span>
                <span style="background:#FFD70020; color:#FFD700; padding:8px 16px; border-radius:20px;">🏆 Top Zone Monthly</span>
                <span style="background:#FF2D5520; color:#FF2D55; padding:8px 16px; border-radius:20px;">📡 Zone Chat</span>
                <span style="background:#FF2D5520; color:#FF2D55; padding:8px 16px; border-radius:20px;">💬 DMs & Stories</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_r:
        tab_login, tab_signup = st.tabs(["🔑 Log In", "✨ Sign Up"])

        with tab_login:
            st.markdown("### Welcome back")
            identifier = st.text_input("Username or Email", key="login_id")
            password = st.text_input("Password", type="password", key="login_pw")
            if st.button("Log In", type="primary", use_container_width=True, key="btn_login"):
                if identifier and password:
                    user = db.authenticate_user(identifier, password)
                    if user:
                        st.session_state.user = user
                        st.success(f"Welcome back, {user['display_name'] or user['username']}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
                else:
                    st.warning("Please fill in all fields.")

        with tab_signup:
            st.markdown("### Create your account")
            col1, col2 = st.columns(2)
            with col1:
                su_username = st.text_input("Username", key="su_user", placeholder="e.g. cooldancer99")
            with col2:
                su_display = st.text_input("Display Name", key="su_display", placeholder="e.g. Cool Dancer")
            su_email = st.text_input("Email", key="su_email")
            countries = get_country_list()
            su_country = st.selectbox("Country", countries, index=countries.index("United States") if "United States" in countries else 0, key="su_country")
            col3, col4 = st.columns(2)
            with col3:
                su_pw = st.text_input("Password", type="password", key="su_pw")
            with col4:
                su_pw2 = st.text_input("Confirm Password", type="password", key="su_pw2")

            if st.button("Create Account", type="primary", use_container_width=True, key="btn_signup"):
                if not all([su_username, su_email, su_country, su_pw, su_pw2]):
                    st.warning("Please fill in all fields.")
                elif su_pw != su_pw2:
                    st.error("Passwords do not match.")
                elif len(su_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                elif len(su_username) < 3:
                    st.error("Username must be at least 3 characters.")
                else:
                    ok, msg = db.create_user(
                        su_username, su_email, su_pw,
                        su_display or su_username,
                        su_country, get_country_code(su_country)
                    )
                    if ok:
                        st.success(msg + " Please log in.")
                    else:
                        st.error(msg)
