import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.helpers import require_login, format_count, time_ago, get_media_path, post_card_css
import json

st.set_page_config(page_title="Explore · Dzone", page_icon="🌍", layout="wide")
st.markdown(post_card_css(), unsafe_allow_html=True)

user = require_login()

st.markdown("# 🌍 Explore")

tab_search, tab_trending, tab_categories, tab_people = st.tabs(
    ["🔍 Search", "🔥 Trending", "📂 Categories", "👥 People"]
)

# ── Search ─────────────────────────────────────────────────────────────────────
with tab_search:
    query = st.text_input("🔍 Search posts, hashtags, or users…", placeholder="#dance, travel, @username")
    if query:
        col_posts, col_users = st.columns([3, 1])
        with col_posts:
            st.markdown("### Posts")
            results = db.search_posts(query)
            if not results:
                st.info("No posts found.")
            for p in results:
                with st.expander(f"@{p['username']} · {p.get('caption','')[:80]}"):
                    mp = get_media_path(p.get("media_path",""))
                    if mp:
                        if p.get("media_type") == "video":
                            st.video(mp)
                        else:
                            st.image(mp, use_container_width=True)
                    st.caption(f"❤️ {format_count(p['likes_count'])}  👁️ {format_count(p['views_count'])}  {time_ago(p['created_at'])}")

        with col_users:
            st.markdown("### Users")
            users = db.search_users(query)
            for u in users:
                av = get_media_path(u.get("avatar_path"))
                verified = "✅" if u.get("is_verified") else ""
                if av:
                    st.image(av, width=40)
                st.markdown(f"**{verified} {u['display_name'] or u['username']}**")
                st.caption(f"@{u['username']} · {u['country']}")
                st.caption(f"👥 {format_count(u['followers_count'])} followers")
                if u["id"] != user["id"]:
                    following = db.is_following(user["id"], u["id"])
                    if st.button("Unfollow" if following else "Follow", key=f"srch_follow_{u['id']}"):
                        db.toggle_follow(user["id"], u["id"])
                        st.rerun()
                st.divider()

# ── Trending ──────────────────────────────────────────────────────────────────
with tab_trending:
    col_tags, col_posts = st.columns([1, 3])
    with col_tags:
        st.markdown("### 🔥 Trending Hashtags")
        tags = db.get_trending_hashtags(limit=15)
        for i, t in enumerate(tags, 1):
            if st.button(f"#{t['hashtag']}  ({format_count(t['total'])})", key=f"tag_{i}"):
                st.session_state.selected_tag = t['hashtag']

    with col_posts:
        tag = st.session_state.get("selected_tag")
        if tag:
            st.markdown(f"### Posts tagged #{tag}")
            tposts = db.search_posts(f"#{tag}")
            for p in tposts:
                mp = get_media_path(p.get("media_path",""))
                with st.container():
                    st.markdown(f"**@{p['username']}** · {time_ago(p['created_at'])}")
                    if mp:
                        if p.get("media_type") == "video":
                            st.video(mp)
                        else:
                            st.image(mp, use_container_width=True)
                    st.caption(p.get("caption",""))
                    st.divider()
        else:
            st.info("Click a hashtag to see posts.")

# ── Categories ────────────────────────────────────────────────────────────────
with tab_categories:
    cats = db.get_categories()
    cat_names = [f"{c['icon']} {c['name']}" for c in cats]
    selected_cat = st.selectbox("Browse by category", cat_names)
    if selected_cat:
        cat_name = selected_cat.split(" ", 1)[1]
        cposts = db.get_posts_by_category(cat_name, limit=12)
        if not cposts:
            st.info(f"No posts in {cat_name} yet.")
        else:
            num_cols = 3
            for i in range(0, len(cposts), num_cols):
                row = cposts[i:i+num_cols]
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
                        st.caption(f"@{p['username']}  ❤️{format_count(p['likes_count'])}")

# ── People ─────────────────────────────────────────────────────────────────────
with tab_people:
    st.markdown("### Suggested People")
    # Get recent active users (not self, not already following)
    conn = db.get_connection()
    suggested = conn.execute(
        """SELECT u.* FROM users u
           WHERE u.id != ?
             AND u.id NOT IN (SELECT following_id FROM follows WHERE follower_id=?)
           ORDER BY u.followers_count DESC LIMIT 20""",
        (user["id"], user["id"])
    ).fetchall()
    conn.close()

    num_cols = 4
    rows = [list(suggested)[i:i+num_cols] for i in range(0, len(suggested), num_cols)]
    for row in rows:
        cols = st.columns(num_cols)
        for j, u_row in enumerate(row):
            u_data = dict(u_row)
            with cols[j]:
                st.markdown('<div class="post-card" style="text-align:center;padding:12px;">', unsafe_allow_html=True)
                av = get_media_path(u_data.get("avatar_path"))
                if av:
                    st.image(av, width=60)
                else:
                    st.markdown("👤", unsafe_allow_html=True)
                verified = "✅" if u_data.get("is_verified") else ""
                st.markdown(f"**{verified}{u_data['display_name'] or u_data['username']}**")
                st.caption(f"@{u_data['username']}")
                st.caption(f"🌍 {u_data['country']}")
                st.caption(f"👥 {format_count(u_data['followers_count'])}")
                following = db.is_following(user["id"], u_data["id"])
                if st.button("Unfollow" if following else "Follow +",
                             key=f"sug_follow_{u_data['id']}", use_container_width=True):
                    db.toggle_follow(user["id"], u_data["id"])
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
