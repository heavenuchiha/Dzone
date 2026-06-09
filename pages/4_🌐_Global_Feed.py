import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.helpers import require_login, format_count, time_ago, get_media_path, post_card_css
import json

st.set_page_config(page_title="Global · Dzone", page_icon="🌐", layout="wide")
st.markdown(post_card_css(), unsafe_allow_html=True)

user = require_login()

st.markdown("# 🌐 Global Feed")
st.caption("Top content from around the world — ranked by engagement")

col_filter, col_main = st.columns([1, 4])

FLAG_MAP = {
    "US": "🇺🇸", "GB": "🇬🇧", "JM": "🇯🇲", "NG": "🇳🇬", "GH": "🇬🇭",
    "IN": "🇮🇳", "CA": "🇨🇦", "AU": "🇦🇺", "BR": "🇧🇷", "DE": "🇩🇪",
    "FR": "🇫🇷", "JP": "🇯🇵", "CN": "🇨🇳", "ZA": "🇿🇦", "MX": "🇲🇽",
    "NG": "🇳🇬", "KE": "🇰🇪", "TT": "🇹🇹", "PH": "🇵🇭", "ID": "🇮🇩",
}

with col_filter:
    st.markdown("### 📂 Filter")
    cats = db.get_categories()
    cat_options = ["All"] + [c["name"] for c in cats]
    selected_cat = st.selectbox("Category", cat_options, key="glob_cat")
    st.markdown("---")
    st.markdown("### 🌍 Filter by Country")
    # Get countries that have posts
    conn = db.get_connection()
    countries_in_db = conn.execute(
        "SELECT DISTINCT country, country_code FROM posts ORDER BY country"
    ).fetchall()
    conn.close()
    country_options = ["All Countries"] + [f"{FLAG_MAP.get(r[1],'🌍')} {r[0]}" for r in countries_in_db]
    selected_country_filter = st.selectbox("Country", country_options, key="glob_country")
    st.markdown("---")
    page_size = st.slider("Posts per page", 5, 30, 15)

with col_main:
    if "global_page" not in st.session_state:
        st.session_state.global_page = 0

    posts = db.get_posts_global(limit=page_size, offset=st.session_state.global_page * page_size)

    # apply filters
    if selected_cat != "All":
        posts = [p for p in posts if p.get("category") == selected_cat]
    if selected_country_filter != "All Countries":
        country_name = selected_country_filter.split(" ", 1)[1].strip()
        posts = [p for p in posts if p.get("country") == country_name]

    if not posts:
        st.info("No posts found with the selected filters.")
    else:
        st.caption(f"Showing {len(posts)} posts from across the globe")

    for p in posts:
        with st.container():
            st.markdown('<div class="post-card">', unsafe_allow_html=True)

            c1, c2 = st.columns([1, 9])
            with c1:
                av = get_media_path(p.get("avatar_path"))
                if av:
                    st.image(av, width=44)
                else:
                    st.markdown("👤")
            with c2:
                verified = "✅ " if p.get("is_verified") else ""
                flag = FLAG_MAP.get(p.get("country_code",""), "🌍")
                st.markdown(f"**{verified}{p.get('display_name') or p.get('username')}** @{p.get('username')}")
                st.caption(f"{flag} {p.get('country','')} · {time_ago(p.get('created_at'))} · {p.get('category','')}")

            caption = p.get("caption", "")
            if caption:
                tags = json.loads(p.get("hashtags", "[]") or "[]")
                for tag in tags:
                    caption = caption.replace(f"#{tag}", f'<span class="hashtag">#{tag}</span>')
                st.markdown(caption, unsafe_allow_html=True)

            mp = get_media_path(p.get("media_path",""))
            if mp:
                if p.get("media_type") == "video":
                    db.increment_views(p["id"])
                    st.video(mp)
                else:
                    st.image(mp, use_container_width=True)
            else:
                st.info("Media not available")

            score = (p.get("likes_count",0) + p.get("comments_count",0)*2 +
                     p.get("shares_count",0)*3 + p.get("saves_count",0)*2)
            st.markdown(
                f'<div class="stat-row">'
                f'❤️ {format_count(p.get("likes_count",0))} &nbsp;'
                f'💬 {format_count(p.get("comments_count",0))} &nbsp;'
                f'🔁 {format_count(p.get("shares_count",0))} &nbsp;'
                f'👁️ {format_count(p.get("views_count",0))} &nbsp;'
                f'🔥 Score: {format_count(score)}'
                f'</div>',
                unsafe_allow_html=True
            )

            a1, a2, a3, a4 = st.columns(4)
            pid = p["id"]
            with a1:
                liked = db.is_liked(user["id"], pid)
                if st.button(f"{'❤️' if liked else '🤍'} Like", key=f"glob_like_{pid}"):
                    db.toggle_like(user["id"], pid)
                    st.rerun()
            with a2:
                saved = db.is_saved(user["id"], pid)
                if st.button(f"{'🔖' if saved else '📌'} Save", key=f"glob_save_{pid}"):
                    db.toggle_save(user["id"], pid)
                    st.rerun()
            with a3:
                if p.get("user_id") != user["id"]:
                    following = db.is_following(user["id"], p.get("user_id",0))
                    if st.button("Unfollow" if following else "➕ Follow", key=f"glob_follow_{pid}"):
                        db.toggle_follow(user["id"], p["user_id"])
                        st.rerun()
            with a4:
                if st.button("🚩 Report", key=f"glob_rep_{pid}"):
                    db.report_content(user["id"], post_id=pid, reason="Reported from global feed")
                    st.toast("Reported.")

            st.markdown('</div>', unsafe_allow_html=True)

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.session_state.global_page > 0:
            if st.button("⬅️ Previous"):
                st.session_state.global_page -= 1
                st.rerun()
    with col_next:
        if len(posts) == page_size:
            if st.button("Next ➡️"):
                st.session_state.global_page += 1
                st.rerun()
