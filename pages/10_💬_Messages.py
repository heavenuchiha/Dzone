import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.helpers import require_login, time_ago, get_media_path, post_card_css

st.set_page_config(page_title="Messages · Dzone", page_icon="💬", layout="wide")
st.markdown(post_card_css(), unsafe_allow_html=True)
st.markdown("""
<style>
.chat-me    { background:#FF2D55; color:#fff; border-radius:18px 18px 4px 18px;
              padding:8px 14px; max-width:65%; margin-left:auto; margin-bottom:4px; }
.chat-other { background:#2A2A2A; color:#fff; border-radius:18px 18px 18px 4px;
              padding:8px 14px; max-width:65%; margin-bottom:4px; }
.conv-item  { background:#1A1A1A; border-radius:10px; padding:12px 16px;
              margin-bottom:6px; cursor:pointer; border:1px solid #2A2A2A; }
.conv-item:hover { border-color:#FF2D55; }
</style>
""", unsafe_allow_html=True)

user = require_login()

st.markdown("# 💬 Messages")

col_list, col_chat = st.columns([1, 3], gap="large")

with col_list:
    st.markdown("### Conversations")

    # Search for a user to DM
    search = st.text_input("🔍 Search users to message", key="dm_search")
    if search:
        results = db.search_users(search, limit=8)
        for u in results:
            if u["id"] != user["id"]:
                av = get_media_path(u.get("avatar_path"))
                c1, c2 = st.columns([1, 4])
                with c1:
                    if av:
                        st.image(av, width=32)
                    else:
                        st.markdown("👤")
                with c2:
                    st.markdown(f"**{u['display_name'] or u['username']}**")
                    st.caption(f"@{u['username']}")
                if st.button("Message", key=f"dm_start_{u['id']}", use_container_width=True):
                    st.session_state.dm_target = u["id"]
                    st.session_state.dm_search = ""
                    st.rerun()
        st.divider()

    # Existing conversations
    convs = db.get_conversations(user["id"])
    if not convs:
        st.info("No conversations yet.")
    for cv in convs:
        av = get_media_path(cv.get("avatar_path"))
        unread = int(cv.get("unread", 0) or 0)
        badge = f" 🔴 {unread}" if unread > 0 else ""
        name = cv.get("display_name") or cv.get("username")
        preview = (cv.get("last_message") or "")[:35]

        is_active = st.session_state.get("dm_target") == cv["id"]
        border = "#FF2D55" if is_active else "#2A2A2A"
        c1, c2 = st.columns([1, 5])
        with c1:
            if av:
                st.image(av, width=36)
            else:
                st.markdown("👤")
        with c2:
            st.markdown(f"**{name}**{badge}")
            st.caption(f"{preview}…")
        if st.button("Open", key=f"open_conv_{cv['id']}", use_container_width=True):
            st.session_state.dm_target = cv["id"]
            st.rerun()

with col_chat:
    target_id = st.session_state.get("dm_target")

    if not target_id:
        st.markdown("""
        <div style="text-align:center; padding:80px 24px; color:#666;">
            <div style="font-size:3rem;">💬</div>
            <div style="font-size:1.2rem; margin-top:12px;">Select a conversation or search for a user</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        target = db.get_user_by_id(target_id)
        if not target:
            st.error("User not found.")
        else:
            av_target = get_media_path(target.get("avatar_path"))
            c1, c2, c3 = st.columns([1, 5, 1])
            with c1:
                if av_target:
                    st.image(av_target, width=44)
                else:
                    st.markdown("👤")
            with c2:
                verified = "✅" if target.get("is_verified") else ""
                st.markdown(f"### {verified} {target['display_name'] or target['username']}")
                st.caption(f"@{target['username']} · {target['country']}")
            with c3:
                if st.button("❌ Close"):
                    st.session_state.dm_target = None
                    st.rerun()

            st.divider()

            messages = db.get_conversation(user["id"], target_id)
            chat_box = st.container(height=420)
            with chat_box:
                if not messages:
                    st.markdown('<div style="text-align:center; color:#666; padding:40px;">Start the conversation!</div>', unsafe_allow_html=True)
                for m in messages:
                    is_me = m["sender_id"] == user["id"]
                    if is_me:
                        st.markdown(
                            f'<div style="display:flex; justify-content:flex-end;">'
                            f'<div class="chat-me">'
                            f'{m["content"]}'
                            f'<div style="font-size:10px;opacity:.6;margin-top:2px;">{time_ago(m["created_at"])}</div>'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f'<div class="chat-other">'
                            f'<div style="font-size:11px;color:#FF2D55;margin-bottom:2px;">@{m["username"]}</div>'
                            f'{m["content"]}'
                            f'<div style="font-size:10px;opacity:.6;margin-top:2px;">{time_ago(m["created_at"])}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

            msg_text = st.text_input("", placeholder=f"Message @{target['username']}…", key="dm_msg_input", label_visibility="collapsed")
            col_send, col_refresh = st.columns([5, 1])
            with col_send:
                if st.button("Send ➤", type="primary", use_container_width=True):
                    if msg_text.strip():
                        db.send_message(user["id"], target_id, msg_text.strip())
                        st.rerun()
            with col_refresh:
                if st.button("🔄"):
                    st.rerun()
