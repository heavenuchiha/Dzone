import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.helpers import (require_login, format_count, time_ago,
                            get_media_path, post_card_css, get_country_list, get_country_code)
import json

st.set_page_config(page_title="My Country · Dzone", page_icon="🗺️", layout="wide")
st.markdown(post_card_css(), unsafe_allow_html=True)

user = require_login()

st.markdown("# 🗺️ My Country Feed")
st.caption(f"Showing content from **{user['country']}** and more")

col_filter, col_main = st.columns([1, 4])

with col_filter:
    st.markdown("### 🌍 Select Country")
    countries = get_country_list()
    default_idx = countries.index(user["country"]) if user["country"] in countries else 0
    selected_country = st.selectbox("Country", countries, index=default_idx)
    country_code = get_country_code(selected_country)
    st.markdown("---")
    st.markdown("### 📂 Category Filter")
    cats = db.get_categories()
    cat_options = ["All"] + [c["name"] for c in cats]
    selected_cat = st.selectbox("Category", cat_options)
    st.markdown("---")
    st.markdown("### 📊 Sort By")
    sort_by = st.radio("Sort", ["Latest", "Most Liked", "Most Viewed"])

with col_main:
    flag_map = {
        "US": "🇺🇸", "GB": "🇬🇧", "JM": "🇯🇲", "NG": "🇳🇬", "GH": "🇬🇭",
        "IN": "🇮🇳", "CA": "🇨🇦", "AU": "🇦🇺", "BR": "🇧🇷", "DE": "🇩🇪",
        "FR": "🇫🇷", "JP": "🇯🇵", "CN": "🇨🇳", "ZA": "🇿🇦", "MX": "🇲🇽",
    }
    flag = flag_map.get(country_code, "🌍")
    st.markdown(f"## {flag} {selected_country}")

    posts = db.get_posts_by_country(country_code, limit=20)

    if selected_cat != "All":
        posts = [p for p in posts if p.get("category") == selected_cat]

    if sort_by == "Most Liked":
        posts = sorted(posts, key=lambda x: x.get("likes_count", 0), reverse=True)
    elif sort_by == "Most Viewed":
        posts = sorted(posts, key=lambda x: x.get("views_count", 0), reverse=True)

    if not posts:
        st.info(f"No posts from {selected_country} yet. Be the first! 🎉")
    else:
        st.caption(f"{len(posts)} posts found")
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
                    st.markdown(f"**{verified}{p.get('display_name') or p.get('username')}** @{p.get('username')}")
                    st.caption(f"{time_ago(p.get('created_at'))} · {p.get('category','')}")

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

                st.markdown(
                    f'<div class="stat-row">❤️ {format_count(p.get("likes_count",0))} &nbsp;'
                    f'💬 {format_count(p.get("comments_count",0))} &nbsp;'
                    f'👁️ {format_count(p.get("views_count",0))}</div>',
                    unsafe_allow_html=True
                )

                a1, a2, a3 = st.columns(3)
                pid = p["id"]
                liked = db.is_liked(user["id"], pid)
                with a1:
                    if st.button(f"{'❤️' if liked else '🤍'} Like", key=f"ctry_like_{pid}"):
                        db.toggle_like(user["id"], pid)
                        st.rerun()
                with a2:
                    saved = db.is_saved(user["id"], pid)
                    if st.button(f"{'🔖' if saved else '📌'} Save", key=f"ctry_save_{pid}"):
                        db.toggle_save(user["id"], pid)
                        st.rerun()
                with a3:
                    if not db.is_following(user["id"], p.get("user_id", 0)) and p.get("user_id") != user["id"]:
                        if st.button("➕ Follow", key=f"ctry_follow_{pid}"):
                            db.toggle_follow(user["id"], p["user_id"])
                            st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)
