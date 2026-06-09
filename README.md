# 📡 Dzone — Social Media Platform

> Connect. Create. Zone In.

Dzone is a full-featured social media web app built with Streamlit. Share videos and photos, explore content from your country or the whole world, compete in monthly Top Zone rankings, and connect with people nearby using the unique **Zone** broadcast chat feature.

---

## Features

| Feature | Description |
|---|---|
| 🏠 For You Feed | Personalized feed + Following tab + Stories |
| 🌍 Explore | Search posts/users, trending hashtags, browse by category |
| 🗺️ My Country | Posts filtered to your country |
| 🌐 Global Feed | Top content from around the world, ranked by engagement |
| 🏆 Top Zone | Monthly top 10 posts per category — resets each month |
| 📡 Zone | Geo-broadcast chat: first 10 people within 1–5 km who accept join your live chat |
| 📤 Upload | Post videos & photos, add Stories (24h), Duets |
| 👤 Profile | View/edit profile, post grid, creator analytics |
| 🔔 Notifications | Likes, comments, follows, zone alerts |
| 💬 Messages | Private DMs between users |

---

## Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/dzone.git
cd dzone
pip install -r requirements.txt
streamlit run app.py
```

---

## Deploy on Streamlit Cloud

1. Push this repo to GitHub (keep `dzone.db` in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → set **Main file path** to `app.py`
4. Click **Deploy**

> **Note:** Streamlit Cloud uses ephemeral storage. The SQLite database and uploaded media reset on each redeploy. For production, replace SQLite with PostgreSQL (e.g. Supabase) and use cloud storage (e.g. Cloudinary or S3) for media files.

---

## Project Structure

```
dzone/
├── app.py                  # Main entry point + auth
├── database.py             # SQLite schema + all queries
├── utils/
│   └── helpers.py          # Utilities: file upload, geo, formatting
├── pages/
│   ├── 1_🏠_Feed.py
│   ├── 2_🌍_Explore.py
│   ├── 3_🗺️_Country_Feed.py
│   ├── 4_🌐_Global_Feed.py
│   ├── 5_🏆_Top_Zone.py
│   ├── 6_📡_Zone.py
│   ├── 7_📤_Upload.py
│   ├── 8_👤_Profile.py
│   ├── 9_🔔_Notifications.py
│   └── 10_💬_Messages.py
├── media/                  # Uploaded files (gitignored)
├── .streamlit/
│   └── config.toml         # Theme config
└── requirements.txt
```

---

## Zone Feature — How It Works

1. Open the **Zone** page and allow location access (or enter coordinates manually)
2. Create a Zone with a topic and set your broadcast radius (1–5 km)
3. Nearby users see your Zone and can request to join
4. The **first 10 people** who join are added to the live group chat
5. The Zone **auto-closes after 10 minutes of inactivity** or when the creator ends it
6. After a Zone ends, members can rate how helpful it was (1–5 stars)

---

## Top Zone — How It Works

- Every post belongs to a **category** (Dance, Comedy, Music, Sports, etc.)
- Each month, posts are scored: `likes + comments×2 + shares×3 + saves×2 + views/10`
- The **top 10** posts per category are shown in the Top Zone hall of fame
- Rankings refresh automatically when you visit the Top Zone page

---

## Tech Stack

- **Frontend/Backend:** Streamlit
- **Database:** SQLite (upgrade to PostgreSQL for production)
- **Media Storage:** Local filesystem (upgrade to Cloudinary/S3 for production)
- **Charts:** Plotly
- **Geolocation:** streamlit-js-eval
