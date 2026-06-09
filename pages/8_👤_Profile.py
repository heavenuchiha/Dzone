import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.helpers import (require_login, format_count, time_ago, get_media_path,
                            post_card_css, save_uploaded_file, get_country_list, get_country_code)
import plotly.graph_objects as go
import json

st.set_page_config(page_title="Profile · Dzone", page_icon="👤", layout="wide")
st.markdown(post_card_css(), unsafe_allow_html=True)
st.markdown("""
<style>
.profile-banner {
    background: linear-gradient(135deg, #FF2D55, #8B0000);
    border-radius: 16px; padding: 32px; text-align: center; margin-bottom: 16px;
}
.stat-card {
    background: #1A1A1A; border-radius: 12px; padding: 16px;
    text-align: center; border: 1px solid #2A2A2A;
}
</style>
""", unsafe_allow_html=True)

current_user = require_login()

# Allow viewing other profiles via query param
query_params = st.query_params
view_username = query_params.get("user", current_user["username"])
profile_user = db.get_user_by_username(view_username) if view_username else current_user
is_own_profile = profile_user and profile_user["id"] == current_user["id"]

if not profile_user:
    st.error("User not found.")
    st.stop()

tab_profile, tab_edit, tab_analytics = (
    st.tabs(["👤 Profile", "✏️ Edit Profile", "📊 Analytics"])
    if is_own_profile else
    (st.tabs(["👤 Profile"]) + [None, None])
)

# ── Profile View ──────────────────────────────────────────────────────────────
with tab_profile:
    # Banner
    av = get_media_path(profile_user.get("avatar_path"))
    verified = "✅" if profile_user.get("is_verified") else ""
    st.markdown(f"""
    <div class="profile-banner">
        <div style="font-size:1.8rem; font-weight:900;">{verified} {profile_user['display_name'] or profile_user['username']}</div>
        <div style="color:#ffccc0;">@{profile_user['username']}</div>
        <div style="color:#ccc; margin-top:4px;">🌍 {profile_user['country']}</div>
    </div>
    """, unsafe_allow_html=True)

    if av:
        col_av, col_stats = st.columns([1, 4])
        with col_av:
            st.image(av, width=100)
    else:
        col_av, col_stats = st.columns([1, 4])
        with col_av:
            st.markdown("👤", unsafe_allow_html=True)

    with col_stats:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Posts", format_count(profile_user["posts_count"]))
        c2.metric("Followers", format_count(profile_user["followers_count"]))
        c3.metric("Following", format_count(profile_user["following_count"]))
        c4.metric("Total Likes", format_count(profile_user.get("total_likes", 0)))

    if profile_user.get("bio"):
        st.markdown(f"> {profile_user['bio']}")

    st.caption(f"Member since {profile_user['created_at'][:10]}")

    if not is_own_profile:
        col_f, col_m, col_b = st.columns(3)
        with col_f:
            following = db.is_following(current_user["id"], profile_user["id"])
            if st.button("Unfollow" if following else "➕ Follow",
                         type="primary" if not following else "secondary",
                         use_container_width=True):
                db.toggle_follow(current_user["id"], profile_user["id"])
                st.rerun()
        with col_m:
            if st.button("💬 Message", use_container_width=True):
                st.session_state.dm_target = profile_user["id"]
                st.switch_page("pages/10_💬_Messages.py")
        with col_b:
            if st.button("🚫 Block", use_container_width=True):
                db.block_user(current_user["id"], profile_user["id"])
                st.warning("User blocked.")

    st.divider()

    # Posts grid
    st.markdown("### Posts")
    posts = db.get_user_posts(profile_user["id"])
    if not posts:
        st.info("No posts yet." if is_own_profile else "This user hasn't posted yet.")
    else:
        grid_tab, list_tab = st.tabs(["⊞ Grid", "≡ List"])
        with grid_tab:
            num_cols = 3
            for i in range(0, len(posts), num_cols):
                row = posts[i:i+num_cols]
                cols = st.columns(num_cols)
                for j, p in enumerate(row):
                    with cols[j]:
                        mp = get_media_path(p.get("thumbnail_path") or p.get("media_path",""))
                        if mp and p.get("media_type") == "image":
                            st.image(mp, use_container_width=True)
                        elif mp and p.get("media_type") == "video":
                            st.video(mp)
                        else:
                            st.markdown("🎬")
                        st.caption(f"❤️{format_count(p['likes_count'])}  👁️{format_count(p['views_count'])}")
        with list_tab:
            for p in posts:
                with st.expander(f"{'🎬' if p['media_type']=='video' else '📸'} {p.get('caption','(no caption)')[:60]}  ·  {time_ago(p['created_at'])}"):
                    mp = get_media_path(p.get("media_path",""))
                    if mp:
                        if p.get("media_type") == "video":
                            st.video(mp)
                        else:
                            st.image(mp, use_container_width=True)
                    tags = json.loads(p.get("hashtags","[]") or "[]")
                    if tags:
                        st.markdown(" ".join([f"`#{t}`" for t in tags]))
                    st.markdown(
                        f'<div class="stat-row">❤️ {format_count(p["likes_count"])} &nbsp;'
                        f'💬 {format_count(p["comments_count"])} &nbsp;'
                        f'👁️ {format_count(p["views_count"])}</div>',
                        unsafe_allow_html=True
                    )
                    if is_own_profile:
                        if st.button("🗑️ Delete", key=f"prof_del_{p['id']}"):
                            db.delete_post(p["id"], current_user["id"])
                            st.rerun()

# ── Edit Profile ──────────────────────────────────────────────────────────────
if is_own_profile and tab_edit:
    with tab_edit:
        st.markdown("### ✏️ Edit Your Profile")
        new_display = st.text_input("Display Name", value=profile_user.get("display_name",""))
        new_bio = st.text_area("Bio", value=profile_user.get("bio",""), max_chars=300)
        countries = get_country_list()
        default_idx = countries.index(profile_user["country"]) if profile_user["country"] in countries else 0
        new_country = st.selectbox("Country", countries, index=default_idx)
        avatar_upload = st.file_uploader("Profile Photo", type=["jpg","jpeg","png","webp"])
        if avatar_upload:
            st.image(avatar_upload, width=100)

        if st.button("💾 Save Changes", type="primary"):
            av_path = None
            if avatar_upload:
                av_path = save_uploaded_file(avatar_upload, "avatars")
            db.update_user_profile(
                current_user["id"], new_display, new_bio,
                new_country, get_country_code(new_country), av_path
            )
            # refresh session
            updated = db.get_user_by_id(current_user["id"])
            st.session_state.user = updated
            st.success("Profile updated!")
            st.rerun()

        st.divider()
        st.markdown("### 🔑 Change Password")
        old_pw = st.text_input("Current Password", type="password", key="old_pw")
        new_pw = st.text_input("New Password", type="password", key="new_pw")
        new_pw2 = st.text_input("Confirm New Password", type="password", key="new_pw2")
        if st.button("Update Password"):
            if not all([old_pw, new_pw, new_pw2]):
                st.warning("Fill all password fields.")
            elif new_pw != new_pw2:
                st.error("New passwords don't match.")
            elif len(new_pw) < 6:
                st.error("Password must be 6+ characters.")
            else:
                auth = db.authenticate_user(current_user["username"], old_pw)
                if auth:
                    conn = db.get_connection()
                    conn.execute(
                        "UPDATE users SET password_hash=? WHERE id=?",
                        (db.hash_password(new_pw), current_user["id"])
                    )
                    conn.commit()
                    conn.close()
                    st.success("Password updated!")
                else:
                    st.error("Current password is incorrect.")

# ── Analytics ─────────────────────────────────────────────────────────────────
if is_own_profile and tab_analytics:
    with tab_analytics:
        st.markdown("### 📊 Creator Analytics")
        stats, user_stats = db.get_user_analytics(current_user["id"])

        if not stats or stats.get("post_count", 0) == 0:
            st.info("Post content to see your analytics.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Posts", format_count(stats.get("post_count", 0)))
            c2.metric("Total Views", format_count(stats.get("total_views", 0)))
            c3.metric("Total Likes", format_count(stats.get("total_likes", 0)))

            c4, c5, c6 = st.columns(3)
            c4.metric("Total Comments", format_count(stats.get("total_comments", 0)))
            c5.metric("Total Shares", format_count(stats.get("total_shares", 0)))
            c6.metric("Total Saves", format_count(stats.get("total_saves", 0)))

            # engagement chart
            st.divider()
            labels = ["Likes", "Comments", "Shares", "Saves"]
            values = [
                stats.get("total_likes", 0) or 0,
                stats.get("total_comments", 0) or 0,
                stats.get("total_shares", 0) or 0,
                stats.get("total_saves", 0) or 0,
            ]
            fig = go.Figure(data=[go.Pie(
                labels=labels, values=values,
                hole=0.4,
                marker=dict(colors=["#FF2D55","#FF6B6B","#FFA07A","#FFD700"])
            )])
            fig.update_layout(
                title="Engagement Breakdown",
                paper_bgcolor="#0A0A0A",
                plot_bgcolor="#0A0A0A",
                font=dict(color="#FFFFFF")
            )
            st.plotly_chart(fig, use_container_width=True)

            # per-post table
            st.markdown("### Post Performance")
            posts_data = db.get_user_posts(current_user["id"], limit=20)
            if posts_data:
                import pandas as pd
                df = pd.DataFrame([{
                    "Caption": (p.get("caption","") or "")[:40],
                    "Type": p.get("media_type",""),
                    "Category": p.get("category",""),
                    "Likes": p.get("likes_count", 0),
                    "Views": p.get("views_count", 0),
                    "Comments": p.get("comments_count", 0),
                    "Date": str(p.get("created_at",""))[:10]
                } for p in posts_data])
                st.dataframe(df, use_container_width=True)
