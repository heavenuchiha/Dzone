import os
import re
import json
import math
import uuid
from datetime import datetime
from PIL import Image
import streamlit as st

MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media")

COUNTRIES = {
    "Afghanistan": "AF", "Albania": "AL", "Algeria": "DZ", "Argentina": "AR",
    "Australia": "AU", "Austria": "AT", "Bangladesh": "BD", "Belgium": "BE",
    "Bolivia": "BO", "Brazil": "BR", "Cambodia": "KH", "Canada": "CA",
    "Chile": "CL", "China": "CN", "Colombia": "CO", "Costa Rica": "CR",
    "Croatia": "HR", "Cuba": "CU", "Czech Republic": "CZ", "Denmark": "DK",
    "Dominican Republic": "DO", "Ecuador": "EC", "Egypt": "EG", "El Salvador": "SV",
    "Ethiopia": "ET", "Finland": "FI", "France": "FR", "Germany": "DE",
    "Ghana": "GH", "Greece": "GR", "Guatemala": "GT", "Haiti": "HT",
    "Honduras": "HN", "Hungary": "HU", "India": "IN", "Indonesia": "ID",
    "Iran": "IR", "Iraq": "IQ", "Ireland": "IE", "Israel": "IL",
    "Italy": "IT", "Jamaica": "JM", "Japan": "JP", "Jordan": "JO",
    "Kenya": "KE", "Malaysia": "MY", "Mexico": "MX", "Morocco": "MA",
    "Mozambique": "MZ", "Netherlands": "NL", "New Zealand": "NZ", "Nicaragua": "NI",
    "Nigeria": "NG", "North Korea": "KP", "Norway": "NO", "Pakistan": "PK",
    "Panama": "PA", "Paraguay": "PY", "Peru": "PE", "Philippines": "PH",
    "Poland": "PL", "Portugal": "PT", "Romania": "RO", "Russia": "RU",
    "Saudi Arabia": "SA", "Senegal": "SN", "Serbia": "RS", "Singapore": "SG",
    "South Africa": "ZA", "South Korea": "KR", "Spain": "ES", "Sri Lanka": "LK",
    "Sweden": "SE", "Switzerland": "CH", "Syria": "SY", "Taiwan": "TW",
    "Tanzania": "TZ", "Thailand": "TH", "Trinidad and Tobago": "TT", "Tunisia": "TN",
    "Turkey": "TR", "Uganda": "UG", "Ukraine": "UA", "United Arab Emirates": "AE",
    "United Kingdom": "GB", "United States": "US", "Uruguay": "UY", "Venezuela": "VE",
    "Vietnam": "VN", "Yemen": "YE", "Zimbabwe": "ZW",
}


def get_country_list():
    return sorted(COUNTRIES.keys())


def get_country_code(country_name):
    return COUNTRIES.get(country_name, "XX")


def save_uploaded_file(uploaded_file, subfolder="images"):
    if uploaded_file is None:
        return None
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    save_dir = os.path.join(MEDIA_DIR, subfolder)
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, filename)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return os.path.join(subfolder, filename)


def make_thumbnail(image_path, size=(400, 400)):
    full = os.path.join(MEDIA_DIR, image_path)
    if not os.path.exists(full):
        return image_path
    try:
        img = Image.open(full)
        img.thumbnail(size, Image.LANCZOS)
        thumb_dir = os.path.join(MEDIA_DIR, "thumbnails")
        os.makedirs(thumb_dir, exist_ok=True)
        name = f"thumb_{uuid.uuid4().hex}.jpg"
        out = os.path.join(thumb_dir, name)
        img.convert("RGB").save(out, "JPEG", quality=80)
        return os.path.join("thumbnails", name)
    except Exception:
        return image_path


def extract_hashtags(text):
    return list(set(re.findall(r'#(\w+)', text.lower())))


def format_count(n):
    if n is None:
        return "0"
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def time_ago(timestamp_str):
    if not timestamp_str:
        return ""
    try:
        ts = datetime.fromisoformat(str(timestamp_str))
    except Exception:
        return str(timestamp_str)
    diff = datetime.now() - ts
    s = diff.total_seconds()
    if s < 60:
        return "just now"
    if s < 3600:
        return f"{int(s//60)}m ago"
    if s < 86400:
        return f"{int(s//3600)}h ago"
    if s < 604800:
        return f"{int(s//86400)}d ago"
    return ts.strftime("%b %d, %Y")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def get_media_path(relative_path):
    if not relative_path:
        return None
    full = os.path.join(MEDIA_DIR, relative_path)
    return full if os.path.exists(full) else None


def require_login():
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Please log in to access this page.")
        st.page_link("app.py", label="Go to Login")
        st.stop()
    return st.session_state.user


def render_avatar(avatar_path, size=40):
    full = get_media_path(avatar_path) if avatar_path else None
    if full:
        return full
    return None


def post_card_css():
    return """
    <style>
    .post-card {
        background: #1A1A1A;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid #2A2A2A;
    }
    .post-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    .username-link {
        font-weight: 700;
        color: #FFFFFF;
        text-decoration: none;
    }
    .category-badge {
        background: #FF2D55;
        color: white;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 12px;
    }
    .stat-row {
        display: flex;
        gap: 16px;
        color: #888;
        font-size: 14px;
        margin-top: 10px;
    }
    .hashtag {
        color: #FF2D55;
    }
    .zone-card {
        background: linear-gradient(135deg, #1A1A2E, #16213E);
        border: 1px solid #FF2D55;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .top-zone-badge {
        background: linear-gradient(135deg, #FFD700, #FFA500);
        color: #000;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
    }
    </style>
    """
