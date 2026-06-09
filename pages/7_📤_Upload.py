import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.helpers import (require_login, save_uploaded_file, make_thumbnail,
                            extract_hashtags, get_country_list, get_country_code,
                            post_card_css, get_media_path)

st.set_page_config(page_title="Upload · Dzone", page_icon="📤", layout="wide")
st.markdown(post_card_css(), unsafe_allow_html=True)

user = require_login()

tab_post, tab_story, tab_saved = st.tabs(["📤 New Post", "📸 Add Story", "🔖 Saved Posts"])

# ── New Post ──────────────────────────────────────────────────────────────────
with tab_post:
    st.markdown("## 📤 Create a New Post")

    col_upload, col_meta = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown("### Media")
        media_type = st.radio("Content type", ["📸 Photo", "🎬 Video"], horizontal=True)
        is_video = "Video" in media_type

        if is_video:
            uploaded = st.file_uploader(
                "Upload video",
                type=["mp4", "mov", "avi", "webm", "mkv"],
                help="Max 500 MB"
            )
        else:
            uploaded = st.file_uploader(
                "Upload photo",
                type=["jpg", "jpeg", "png", "gif", "webp"],
                help="Max 200 MB"
            )

        if uploaded:
            if is_video:
                st.video(uploaded)
            else:
                st.image(uploaded, use_container_width=True)

    with col_meta:
        st.markdown("### Post Details")
        caption = st.text_area(
            "Caption",
            placeholder="Write a caption… use #hashtags to reach more people!",
            height=100,
            max_chars=2200
        )
        st.caption(f"{len(caption)}/2200")

        cats = db.get_categories()
        cat_options = [f"{c['icon']} {c['name']}" for c in cats]
        selected_cat = st.selectbox("Category", cat_options)
        cat_name = selected_cat.split(" ", 1)[1]

        countries = get_country_list()
        default_idx = countries.index(user["country"]) if user["country"] in countries else 0
        post_country = st.selectbox("Post Country", countries, index=default_idx)

        sound_name = st.text_input("Sound / Music (optional)", placeholder="e.g. Trending Beat 2025")

        # duet option
        is_duet = st.checkbox("🎭 This is a Duet")
        original_post_id = None
        if is_duet:
            original_post_id = st.number_input("Original Post ID", min_value=1, step=1)

        hashtags = extract_hashtags(caption)
        if hashtags:
            st.markdown("**Detected hashtags:** " + " ".join([f"`#{h}`" for h in hashtags]))

        if st.button("📤 Publish Post", type="primary", use_container_width=True):
            if not uploaded:
                st.error("Please upload a file.")
            elif not caption.strip() and not is_video:
                st.warning("Consider adding a caption.")
            else:
                with st.spinner("Uploading…"):
                    subfolder = "videos" if is_video else "images"
                    media_path = save_uploaded_file(uploaded, subfolder)

                    thumbnail_path = ""
                    if not is_video and media_path:
                        thumbnail_path = make_thumbnail(media_path)

                    if media_path:
                        post_id = db.create_post(
                            user_id=user["id"],
                            media_type="video" if is_video else "image",
                            media_path=media_path,
                            thumbnail_path=thumbnail_path,
                            caption=caption,
                            category=cat_name,
                            hashtags=hashtags,
                            country=post_country,
                            country_code=get_country_code(post_country),
                            sound_name=sound_name,
                            is_duet=1 if is_duet else 0,
                            original_post_id=int(original_post_id) if is_duet and original_post_id else None
                        )
                        st.success(f"✅ Post published! Post ID: #{post_id}")
                        st.balloons()
                    else:
                        st.error("Upload failed. Please try again.")

# ── Story ─────────────────────────────────────────────────────────────────────
with tab_story:
    st.markdown("## 📸 Add a Story")
    st.info("Stories disappear after 24 hours.")

    story_upload = st.file_uploader(
        "Photo or Short Video",
        type=["jpg", "jpeg", "png", "mp4", "mov"],
        key="story_upload"
    )
    story_caption = st.text_input("Caption (optional)", key="story_caption")

    if story_upload:
        if story_upload.type.startswith("video"):
            st.video(story_upload)
        else:
            st.image(story_upload, use_container_width=True)

    if st.button("📸 Post Story", type="primary", use_container_width=True):
        if not story_upload:
            st.error("Please upload a file.")
        else:
            with st.spinner("Uploading story…"):
                is_v = story_upload.type.startswith("video")
                mpath = save_uploaded_file(story_upload, "stories")
                if mpath:
                    db.create_story(user["id"], "video" if is_v else "image", mpath, story_caption)
                    st.success("Story posted! It will disappear in 24 hours. 🕐")
                else:
                    st.error("Upload failed.")

# ── Saved Posts ───────────────────────────────────────────────────────────────
with tab_saved:
    st.markdown("## 🔖 Your Saved Posts")
    saved = db.get_saved_posts(user["id"])
    if not saved:
        st.info("You haven't saved any posts yet.")
    else:
        st.caption(f"{len(saved)} saved posts")
        num_cols = 3
        for i in range(0, len(saved), num_cols):
            row = saved[i:i+num_cols]
            cols = st.columns(num_cols)
            for j, p in enumerate(row):
                with cols[j]:
                    mp = get_media_path(p.get("thumbnail_path") or p.get("media_path",""))
                    if mp and p.get("media_type") == "image":
                        st.image(mp, use_container_width=True)
                    elif mp and p.get("media_type") == "video":
                        st.video(mp)
                    st.caption(f"@{p['username']}  ❤️{p['likes_count']}")
                    if st.button("🗑️ Unsave", key=f"unsave_{p['id']}"):
                        db.toggle_save(user["id"], p["id"])
                        st.rerun()
