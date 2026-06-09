import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.helpers import require_login, format_count, time_ago, get_media_path, post_card_css
from datetime import datetime

st.set_page_config(page_title="Top Zone · Dzone", page_icon="🏆", layout="wide")
st.markdown(post_card_css(), unsafe_allow_html=True)
st.markdown("""
<style>
.topzone-header {
    background: linear-gradient(135deg, #1a0a00, #3d1a00);
    border: 1px solid #FFD700;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin-bottom: 24px;
}
.rank-1 { background: linear-gradient(135deg, #FFD700, #FFA500); color:#000; }
.rank-2 { background: linear-gradient(135deg, #C0C0C0, #A0A0A0); color:#000; }
.rank-3 { background: linear-gradient(135deg, #CD7F32, #A0522D); color:#fff; }
.rank-other { background: #2A2A2A; color:#fff; }
.rank-badge {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 16px; margin: 0 auto 8px;
}
</style>
""", unsafe_allow_html=True)

user = require_login()

# Auto-run top zone computation on load
now = datetime.now()
db.compute_top_zone(now.month, now.year)

st.markdown("""
<div class="topzone-header">
    <div style="font-size:2.5rem;">🏆</div>
    <div style="font-size:1.8rem; font-weight:900; color:#FFD700;">TOP ZONE</div>
    <div style="color:#ccc; margin-top:4px;">Monthly Top 10 in Every Category</div>
</div>
""", unsafe_allow_html=True)

# Month/year selector
col_m, col_y, col_cat = st.columns(3)
months = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]
with col_m:
    selected_month = st.selectbox("Month", months, index=now.month - 1)
with col_y:
    year_opts = list(range(2024, now.year + 1))
    selected_year = st.selectbox("Year", year_opts, index=len(year_opts)-1)
with col_cat:
    month_num = months.index(selected_month) + 1
    top_cats = db.get_top_zone_categories(month_num, selected_year)
    if not top_cats:
        top_cats = [c["name"] for c in db.get_categories()]
    selected_view = st.selectbox("Category", ["All Categories"] + top_cats)

st.divider()

RANK_ICONS = {1: "🥇", 2: "🥈", 3: "🥉"}

def render_top_post(p, rank, cat_name):
    icon = RANK_ICONS.get(rank, f"#{rank}")
    rank_class = {1: "rank-1", 2: "rank-2", 3: "rank-3"}.get(rank, "rank-other")

    with st.container():
        st.markdown(f'<div class="post-card">', unsafe_allow_html=True)
        header_col, content_col = st.columns([1, 4])

        with header_col:
            st.markdown(
                f'<div class="rank-badge {rank_class}">{icon}</div>',
                unsafe_allow_html=True
            )
            st.markdown(f'<div class="top-zone-badge">{cat_name}</div>', unsafe_allow_html=True)
            st.metric("Score", format_count(p.get("score", 0)))

        with content_col:
            c1, c2 = st.columns([1, 6])
            with c1:
                av = get_media_path(p.get("avatar_path"))
                if av:
                    st.image(av, width=44)
                else:
                    st.markdown("👤")
            with c2:
                verified = "✅ " if p.get("is_verified") else ""
                st.markdown(f"**{verified}{p.get('display_name') or p.get('username')}** @{p.get('username')}")
                st.caption(f"{time_ago(p.get('created_at'))}")

            caption = p.get("caption", "")
            if caption:
                st.markdown(caption[:200])

            mp = get_media_path(p.get("media_path",""))
            if mp:
                if p.get("media_type") == "video":
                    db.increment_views(p["id"])
                    st.video(mp)
                else:
                    st.image(mp, use_container_width=True)
            else:
                st.info("Media unavailable")

            st.markdown(
                f'<div class="stat-row">'
                f'❤️ {format_count(p.get("likes_count",0))} &nbsp;'
                f'💬 {format_count(p.get("comments_count",0))} &nbsp;'
                f'🔁 {format_count(p.get("shares_count",0))} &nbsp;'
                f'👁️ {format_count(p.get("views_count",0))}'
                f'</div>',
                unsafe_allow_html=True
            )

            pid = p["id"]
            liked = db.is_liked(user["id"], pid)
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(f"{'❤️' if liked else '🤍'} Like", key=f"tz_like_{pid}_{rank}"):
                    db.toggle_like(user["id"], pid)
                    st.rerun()
            with col_b:
                saved = db.is_saved(user["id"], pid)
                if st.button(f"{'🔖' if saved else '📌'} Save", key=f"tz_save_{pid}_{rank}"):
                    db.toggle_save(user["id"], pid)
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


if selected_view == "All Categories":
    cats_to_show = top_cats
    for cat_name in cats_to_show:
        posts = db.get_top_zone(month_num, selected_year, category=cat_name)
        if not posts:
            continue
        cat_info = next((c for c in db.get_categories() if c["name"] == cat_name), {})
        icon = cat_info.get("icon","🎬")
        st.markdown(f"## {icon} {cat_name}")
        tab_cols = st.columns(min(3, len(posts)))
        for i, p in enumerate(posts[:3]):
            with tab_cols[i]:
                rank = p.get("rank", i+1)
                ri = RANK_ICONS.get(rank, f"#{rank}")
                st.markdown(f"**{ri} Rank #{rank}**")
                mp = get_media_path(p.get("thumbnail_path") or p.get("media_path",""))
                if mp and p.get("media_type") == "image":
                    st.image(mp, use_container_width=True)
                elif mp and p.get("media_type") == "video":
                    st.video(mp)
                st.caption(f"@{p['username']} · ❤️{format_count(p['likes_count'])}")
        if len(posts) > 3:
            with st.expander(f"See full top 10 for {cat_name}"):
                for p in posts:
                    render_top_post(p, p.get("rank",1), cat_name)
        st.divider()
else:
    cat_name = selected_view
    posts = db.get_top_zone(month_num, selected_year, category=cat_name)
    if not posts:
        st.info(f"No top zone data for {cat_name} in {selected_month} {selected_year}.\nPosts are ranked at the start of each month.")
    else:
        cat_info = next((c for c in db.get_categories() if c["name"] == cat_name), {})
        icon = cat_info.get("icon","🎬")
        st.markdown(f"## {icon} Top 10 · {cat_name} · {selected_month} {selected_year}")
        for p in posts:
            render_top_post(p, p.get("rank",1), cat_name)
