import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
import json
from utils.helpers import (require_login, format_count, time_ago,
                            get_media_path, post_card_css)

st.set_page_config(page_title="Feed · Dzone", page_icon="🏠", layout="wide")
st.markdown(post_card_css(), unsafe_allow_html=True)

user = require_login()

st.markdown("# 🏠 For You")

tab_foryou, tab_following, tab_stories = st.tabs(["✨ For You", "👥 Following", "📸 Stories"])

# ── helper ────────────────────────────────────────────────────────────────────

def render_post(p, show_actions=True):
    with st.container():
        st.markdown('<div class="post-card">', unsafe_allow_html=True)

        # header
        c1, c2 = st.columns([1, 8])
        with c1:
            av = get_media_path(p.get("avatar_path"))
            if av:
                st.image(av, width=44)
            else:
                st.markdown("👤")
        with c2:
            verified = "✅ " if p.get("is_verified") else ""
            st.markdown(f"**{verified}{p.get('display_name') or p.get('username')}** @{p.get('username')}")
            st.caption(f"{time_ago(p.get('created_at'))} · {p.get('country','')}")

        # category
        cat = p.get("category", "General")
        st.markdown(f'<span class="category-badge">{cat}</span>', unsafe_allow_html=True)

        # caption + hashtags
        caption = p.get("caption", "")
        if caption:
            tags = json.loads(p.get("hashtags", "[]") or "[]")
            for tag in tags:
                caption = caption.replace(f"#{tag}", f'<span class="hashtag">#{tag}</span>')
            st.markdown(caption, unsafe_allow_html=True)

        # media
        media_path = get_media_path(p.get("media_path", ""))
        if media_path:
            if p.get("media_type") == "video":
                db.increment_views(p["id"])
                st.video(media_path)
            else:
                st.image(media_path, use_container_width=True)
        else:
            st.info("Media not available")

        # stats row
        st.markdown(
            f'<div class="stat-row">'
            f'❤️ {format_count(p.get("likes_count",0))} &nbsp;'
            f'💬 {format_count(p.get("comments_count",0))} &nbsp;'
            f'🔁 {format_count(p.get("shares_count",0))} &nbsp;'
            f'🔖 {format_count(p.get("saves_count",0))} &nbsp;'
            f'👁️ {format_count(p.get("views_count",0))}'
            f'</div>',
            unsafe_allow_html=True
        )

        if show_actions:
            a1, a2, a3, a4, a5 = st.columns(5)
            pid = p["id"]
            liked = db.is_liked(user["id"], pid)
            saved = db.is_saved(user["id"], pid)

            with a1:
                if st.button(f"{'❤️' if liked else '🤍'} Like", key=f"like_{pid}"):
                    db.toggle_like(user["id"], pid)
                    st.rerun()
            with a2:
                if st.button("💬 Comment", key=f"cmt_open_{pid}"):
                    st.session_state[f"show_comments_{pid}"] = not st.session_state.get(f"show_comments_{pid}", False)
            with a3:
                if st.button(f"{'🔖' if saved else '📌'} Save", key=f"save_{pid}"):
                    db.toggle_save(user["id"], pid)
                    st.rerun()
            with a4:
                if st.button("🚩 Report", key=f"rep_{pid}"):
                    db.report_content(user["id"], post_id=pid, reason="Reported by user")
                    st.toast("Reported. We'll review it.")
            with a5:
                owner = p.get("user_id") == user["id"]
                if owner:
                    if st.button("🗑️ Delete", key=f"del_{pid}"):
                        db.delete_post(pid, user["id"])
                        st.rerun()

            # inline comments
            if st.session_state.get(f"show_comments_{pid}", False):
                comments = db.get_comments(pid)
                st.markdown("---")
                for c in comments:
                    av_c = get_media_path(c.get("avatar_path"))
                    prefix = f"![av]({av_c})" if av_c else "👤"
                    st.markdown(f"{prefix} **@{c['username']}** · {time_ago(c['created_at'])}")
                    st.markdown(f"> {c['content']}")
                new_comment = st.text_input("Add a comment…", key=f"cmt_{pid}")
                if st.button("Post", key=f"cmt_post_{pid}"):
                    if new_comment.strip():
                        db.add_comment(user["id"], pid, new_comment.strip())
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ── For You tab ───────────────────────────────────────────────────────────────
with tab_foryou:
    if "foryou_page" not in st.session_state:
        st.session_state.foryou_page = 0

    posts = db.get_posts_feed(limit=10, offset=st.session_state.foryou_page * 10)
    if not posts:
        st.info("No posts yet. Be the first to post! 🎉")
    for p in posts:
        render_post(p)

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.session_state.foryou_page > 0:
            if st.button("⬅️ Previous", key="fy_prev"):
                st.session_state.foryou_page -= 1
                st.rerun()
    with col_next:
        if len(posts) == 10:
            if st.button("Next ➡️", key="fy_next"):
                st.session_state.foryou_page += 1
                st.rerun()

# ── Following tab ─────────────────────────────────────────────────────────────
with tab_following:
    if "following_page" not in st.session_state:
        st.session_state.following_page = 0

    fposts = db.get_following_posts(user["id"], limit=10, offset=st.session_state.following_page * 10)
    if not fposts:
        st.info("Follow people to see their posts here.")
        st.page_link("pages/2_🌍_Explore.py", label="🌍 Discover people to follow")
    for p in fposts:
        render_post(p)

    col_prev2, col_next2 = st.columns(2)
    with col_prev2:
        if st.session_state.following_page > 0:
            if st.button("⬅️ Previous", key="fl_prev"):
                st.session_state.following_page -= 1
                st.rerun()
    with col_next2:
        if len(fposts) == 10:
            if st.button("Next ➡️", key="fl_next"):
                st.session_state.following_page += 1
                st.rerun()

# ── Stories tab ───────────────────────────────────────────────────────────────
with tab_stories:
    stories = db.get_active_stories_by_following(user["id"])
    if not stories:
        st.info("No active stories from people you follow.")
    else:
        cols = st.columns(min(len(stories), 5))
        for i, s in enumerate(stories[:5]):
            with cols[i]:
                av = get_media_path(s.get("avatar_path"))
                if av:
                    st.image(av, width=60)
                st.caption(f"@{s['username']}")
                if st.button("View", key=f"story_{s['id']}"):
                    st.session_state.view_story = s
                    db.view_story(s["id"], user["id"])

        if "view_story" in st.session_state and st.session_state.view_story:
            s = st.session_state.view_story
            st.divider()
            st.markdown(f"**@{s['username']}**'s Story · {time_ago(s['created_at'])}")
            mp = get_media_path(s.get("media_path",""))
            if mp:
                if s.get("media_type") == "video":
                    st.video(mp)
                else:
                    st.image(mp, use_container_width=True)
            if s.get("caption"):
                st.markdown(s["caption"])
            if st.button("Close Story"):
                del st.session_state.view_story
                st.rerun()
