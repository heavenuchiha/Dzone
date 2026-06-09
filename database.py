import sqlite3
import os
import hashlib
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "dzone.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            bio TEXT DEFAULT '',
            avatar_path TEXT DEFAULT '',
            country TEXT DEFAULT 'Unknown',
            country_code TEXT DEFAULT 'XX',
            is_verified INTEGER DEFAULT 0,
            is_private INTEGER DEFAULT 0,
            followers_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            posts_count INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            media_type TEXT NOT NULL,
            media_path TEXT NOT NULL,
            thumbnail_path TEXT DEFAULT '',
            caption TEXT DEFAULT '',
            category TEXT DEFAULT 'General',
            hashtags TEXT DEFAULT '[]',
            country TEXT DEFAULT 'Unknown',
            country_code TEXT DEFAULT 'XX',
            sound_name TEXT DEFAULT '',
            is_duet INTEGER DEFAULT 0,
            original_post_id INTEGER,
            likes_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            shares_count INTEGER DEFAULT 0,
            saves_count INTEGER DEFAULT 0,
            views_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            media_type TEXT NOT NULL,
            media_path TEXT NOT NULL,
            caption TEXT DEFAULT '',
            views_count INTEGER DEFAULT 0,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS story_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            viewer_id INTEGER NOT NULL,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(story_id, viewer_id)
        );

        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, post_id)
        );

        CREATE TABLE IF NOT EXISTS saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, post_id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            parent_id INTEGER,
            content TEXT NOT NULL,
            likes_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS comment_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            comment_id INTEGER NOT NULL,
            UNIQUE(user_id, comment_id)
        );

        CREATE TABLE IF NOT EXISTS follows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower_id INTEGER NOT NULL,
            following_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(follower_id, following_id)
        );

        CREATE TABLE IF NOT EXISTS zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            radius_km REAL DEFAULT 3.0,
            status TEXT DEFAULT 'active',
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            rating_avg REAL DEFAULT 0,
            rating_count INTEGER DEFAULT 0,
            FOREIGN KEY (creator_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS zone_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(zone_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS zone_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(zone_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS zone_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS zone_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(zone_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            from_user_id INTEGER,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            post_id INTEGER,
            zone_id INTEGER,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            icon TEXT DEFAULT '🎬',
            description TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS top_zone_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            rank INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            score INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS hashtag_trending (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hashtag TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            date DATE DEFAULT (DATE('now')),
            UNIQUE(hashtag, date)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            media_path TEXT DEFAULT '',
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER NOT NULL,
            post_id INTEGER,
            reported_user_id INTEGER,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blocker_id INTEGER NOT NULL,
            blocked_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(blocker_id, blocked_id)
        );
    """)

    default_cats = [
        ('Dance', '💃', 'Dance and choreography'),
        ('Comedy', '😂', 'Funny and entertaining content'),
        ('Music', '🎵', 'Music performances and covers'),
        ('Sports', '⚽', 'Sports highlights and tricks'),
        ('Food', '🍔', 'Cooking and food reviews'),
        ('Travel', '✈️', 'Travel vlogs and destinations'),
        ('Fashion', '👗', 'Style and fashion content'),
        ('Education', '📚', 'Educational and informative'),
        ('Gaming', '🎮', 'Gaming highlights and reviews'),
        ('Art', '🎨', 'Art and creative content'),
        ('Fitness', '💪', 'Workout and fitness'),
        ('Pets', '🐾', 'Cute and funny pets'),
        ('Nature', '🌿', 'Nature and wildlife'),
        ('Technology', '💻', 'Tech reviews and tutorials'),
        ('General', '📱', 'General content'),
    ]
    for cat in default_cats:
        try:
            c.execute("INSERT OR IGNORE INTO categories (name, icon, description) VALUES (?,?,?)", cat)
        except Exception:
            pass

    conn.commit()
    conn.close()


# ─── Auth ────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, email, password, display_name, country, country_code):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username,email,password_hash,display_name,country,country_code) VALUES (?,?,?,?,?,?)",
            (username.lower(), email.lower(), hash_password(password), display_name, country, country_code)
        )
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already taken."
        return False, "Email already registered."
    finally:
        conn.close()


def authenticate_user(identifier, password):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE (username=? OR email=?) AND password_hash=?",
        (identifier.lower(), identifier.lower(), hash_password(password))
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_username(username):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username.lower(),)).fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_profile(user_id, display_name, bio, country, country_code, avatar_path=None):
    conn = get_connection()
    if avatar_path:
        conn.execute(
            "UPDATE users SET display_name=?,bio=?,country=?,country_code=?,avatar_path=? WHERE id=?",
            (display_name, bio, country, country_code, avatar_path, user_id)
        )
    else:
        conn.execute(
            "UPDATE users SET display_name=?,bio=?,country=?,country_code=? WHERE id=?",
            (display_name, bio, country, country_code, user_id)
        )
    conn.commit()
    conn.close()


# ─── Posts ───────────────────────────────────────────────────────────────────

def create_post(user_id, media_type, media_path, thumbnail_path, caption, category,
                hashtags, country, country_code, sound_name="", is_duet=0, original_post_id=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO posts
           (user_id,media_type,media_path,thumbnail_path,caption,category,hashtags,
            country,country_code,sound_name,is_duet,original_post_id)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user_id, media_type, media_path, thumbnail_path, caption, category,
         json.dumps(hashtags), country, country_code, sound_name, is_duet, original_post_id)
    )
    post_id = c.lastrowid
    conn.execute("UPDATE users SET posts_count=posts_count+1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    # update trending hashtags
    _update_trending_hashtags(hashtags)
    return post_id


def _update_trending_hashtags(hashtags):
    if not hashtags:
        return
    conn = get_connection()
    for tag in hashtags:
        tag = tag.lstrip('#').lower()
        if tag:
            try:
                conn.execute(
                    "INSERT INTO hashtag_trending (hashtag, count) VALUES (?,1) "
                    "ON CONFLICT(hashtag,date) DO UPDATE SET count=count+1",
                    (tag,)
                )
            except Exception:
                pass
    conn.commit()
    conn.close()


def get_posts_feed(limit=20, offset=0, exclude_user_id=None):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_path, u.is_verified, u.country
           FROM posts p JOIN users u ON p.user_id=u.id
           WHERE (? IS NULL OR p.user_id != ?)
           ORDER BY p.created_at DESC LIMIT ? OFFSET ?""",
        (exclude_user_id, exclude_user_id, limit, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_posts_by_country(country_code, limit=20, offset=0):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_path, u.is_verified
           FROM posts p JOIN users u ON p.user_id=u.id
           WHERE p.country_code=?
           ORDER BY p.created_at DESC LIMIT ? OFFSET ?""",
        (country_code, limit, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_posts_global(limit=20, offset=0):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_path, u.is_verified, u.country
           FROM posts p JOIN users u ON p.user_id=u.id
           ORDER BY (p.likes_count + p.comments_count * 2 + p.shares_count * 3) DESC,
                    p.created_at DESC LIMIT ? OFFSET ?""",
        (limit, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_following_posts(user_id, limit=20, offset=0):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_path, u.is_verified
           FROM posts p JOIN users u ON p.user_id=u.id
           WHERE p.user_id IN (SELECT following_id FROM follows WHERE follower_id=?)
           ORDER BY p.created_at DESC LIMIT ? OFFSET ?""",
        (user_id, limit, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_posts_by_category(category, limit=20, offset=0):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_path, u.is_verified
           FROM posts p JOIN users u ON p.user_id=u.id
           WHERE p.category=?
           ORDER BY p.created_at DESC LIMIT ? OFFSET ?""",
        (category, limit, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_posts(user_id, limit=50, offset=0):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_path, u.is_verified
           FROM posts p JOIN users u ON p.user_id=u.id
           WHERE p.user_id=? ORDER BY p.created_at DESC LIMIT ? OFFSET ?""",
        (user_id, limit, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_saved_posts(user_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_path, u.is_verified
           FROM saves s
           JOIN posts p ON s.post_id=p.id
           JOIN users u ON p.user_id=u.id
           WHERE s.user_id=? ORDER BY s.created_at DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_posts(query, limit=20):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_path, u.is_verified
           FROM posts p JOIN users u ON p.user_id=u.id
           WHERE p.caption LIKE ? OR p.hashtags LIKE ?
           ORDER BY p.created_at DESC LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_users(query, limit=20):
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM users
           WHERE username LIKE ? OR display_name LIKE ?
           LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def increment_views(post_id):
    conn = get_connection()
    conn.execute("UPDATE posts SET views_count=views_count+1 WHERE id=?", (post_id,))
    conn.commit()
    conn.close()


def delete_post(post_id, user_id):
    conn = get_connection()
    conn.execute("DELETE FROM posts WHERE id=? AND user_id=?", (post_id, user_id))
    conn.execute("UPDATE users SET posts_count=MAX(posts_count-1,0) WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


# ─── Likes ───────────────────────────────────────────────────────────────────

def toggle_like(user_id, post_id):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id)).fetchone()
    if existing:
        conn.execute("DELETE FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        conn.execute("UPDATE posts SET likes_count=MAX(likes_count-1,0) WHERE id=?", (post_id,))
        liked = False
    else:
        conn.execute("INSERT OR IGNORE INTO likes (user_id,post_id) VALUES (?,?)", (user_id, post_id))
        conn.execute("UPDATE posts SET likes_count=likes_count+1 WHERE id=?", (post_id,))
        liked = True
        # notify post owner
        post = conn.execute("SELECT user_id FROM posts WHERE id=?", (post_id,)).fetchone()
        if post and post[0] != user_id:
            _create_notification_conn(conn, post[0], user_id, 'like', 'liked your post', post_id=post_id)
    conn.commit()
    conn.close()
    return liked


def is_liked(user_id, post_id):
    conn = get_connection()
    r = conn.execute("SELECT id FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id)).fetchone()
    conn.close()
    return r is not None


def toggle_save(user_id, post_id):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM saves WHERE user_id=? AND post_id=?", (user_id, post_id)).fetchone()
    if existing:
        conn.execute("DELETE FROM saves WHERE user_id=? AND post_id=?", (user_id, post_id))
        conn.execute("UPDATE posts SET saves_count=MAX(saves_count-1,0) WHERE id=?", (post_id,))
        saved = False
    else:
        conn.execute("INSERT OR IGNORE INTO saves (user_id,post_id) VALUES (?,?)", (user_id, post_id))
        conn.execute("UPDATE posts SET saves_count=saves_count+1 WHERE id=?", (post_id,))
        saved = True
    conn.commit()
    conn.close()
    return saved


def is_saved(user_id, post_id):
    conn = get_connection()
    r = conn.execute("SELECT id FROM saves WHERE user_id=? AND post_id=?", (user_id, post_id)).fetchone()
    conn.close()
    return r is not None


# ─── Comments ────────────────────────────────────────────────────────────────

def add_comment(user_id, post_id, content, parent_id=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO comments (user_id,post_id,parent_id,content) VALUES (?,?,?,?)",
        (user_id, post_id, parent_id, content)
    )
    conn.execute("UPDATE posts SET comments_count=comments_count+1 WHERE id=?", (post_id,))
    post = conn.execute("SELECT user_id FROM posts WHERE id=?", (post_id,)).fetchone()
    if post and post[0] != user_id:
        _create_notification_conn(conn, post[0], user_id, 'comment', 'commented on your post', post_id=post_id)
    conn.commit()
    conn.close()


def get_comments(post_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.*, u.username, u.display_name, u.avatar_path, u.is_verified
           FROM comments c JOIN users u ON c.user_id=u.id
           WHERE c.post_id=? AND c.parent_id IS NULL
           ORDER BY c.created_at DESC""",
        (post_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Follows ─────────────────────────────────────────────────────────────────

def toggle_follow(follower_id, following_id):
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM follows WHERE follower_id=? AND following_id=?",
        (follower_id, following_id)
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        conn.execute("UPDATE users SET followers_count=MAX(followers_count-1,0) WHERE id=?", (following_id,))
        conn.execute("UPDATE users SET following_count=MAX(following_count-1,0) WHERE id=?", (follower_id,))
        following = False
    else:
        conn.execute("INSERT OR IGNORE INTO follows (follower_id,following_id) VALUES (?,?)", (follower_id, following_id))
        conn.execute("UPDATE users SET followers_count=followers_count+1 WHERE id=?", (following_id,))
        conn.execute("UPDATE users SET following_count=following_count+1 WHERE id=?", (follower_id,))
        following = True
        _create_notification_conn(conn, following_id, follower_id, 'follow', 'started following you')
    conn.commit()
    conn.close()
    return following


def is_following(follower_id, following_id):
    conn = get_connection()
    r = conn.execute(
        "SELECT id FROM follows WHERE follower_id=? AND following_id=?",
        (follower_id, following_id)
    ).fetchone()
    conn.close()
    return r is not None


# ─── Stories ─────────────────────────────────────────────────────────────────

def create_story(user_id, media_type, media_path, caption):
    expires = datetime.now() + timedelta(hours=24)
    conn = get_connection()
    conn.execute(
        "INSERT INTO stories (user_id,media_type,media_path,caption,expires_at) VALUES (?,?,?,?,?)",
        (user_id, media_type, media_path, caption, expires.isoformat())
    )
    conn.commit()
    conn.close()


def get_active_stories_by_following(user_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, u.username, u.display_name, u.avatar_path
           FROM stories s JOIN users u ON s.user_id=u.id
           WHERE s.user_id IN (SELECT following_id FROM follows WHERE follower_id=?)
             AND s.expires_at > CURRENT_TIMESTAMP
           ORDER BY s.created_at DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def view_story(story_id, viewer_id):
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO story_views (story_id,viewer_id) VALUES (?,?)", (story_id, viewer_id))
        conn.execute("UPDATE stories SET views_count=views_count+1 WHERE id=?", (story_id,))
    except Exception:
        pass
    conn.commit()
    conn.close()


# ─── Zones ───────────────────────────────────────────────────────────────────

def create_zone(creator_id, title, description, latitude, longitude, radius_km):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO zones (creator_id,title,description,latitude,longitude,radius_km)
           VALUES (?,?,?,?,?,?)""",
        (creator_id, title, description, latitude, longitude, radius_km)
    )
    zone_id = c.lastrowid
    # creator auto-joins
    conn.execute("INSERT OR IGNORE INTO zone_members (zone_id,user_id) VALUES (?,?)", (zone_id, creator_id))
    conn.commit()
    conn.close()
    return zone_id


def get_nearby_zones(latitude, longitude, radius_km=50):
    """Return active zones within radius_km using bounding box approximation."""
    conn = get_connection()
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(abs(latitude) * 0.0174533, 0.001))
    rows = conn.execute(
        """SELECT z.*, u.username, u.display_name, u.avatar_path,
                  (SELECT COUNT(*) FROM zone_members WHERE zone_id=z.id) as member_count
           FROM zones z JOIN users u ON z.creator_id=u.id
           WHERE z.status='active'
             AND z.latitude BETWEEN ? AND ?
             AND z.longitude BETWEEN ? AND ?
           ORDER BY z.created_at DESC""",
        (latitude - lat_delta, latitude + lat_delta,
         longitude - lon_delta, longitude + lon_delta)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_zone(zone_id):
    conn = get_connection()
    row = conn.execute(
        """SELECT z.*, u.username, u.display_name, u.avatar_path,
                  (SELECT COUNT(*) FROM zone_members WHERE zone_id=z.id) as member_count
           FROM zones z JOIN users u ON z.creator_id=u.id WHERE z.id=?""",
        (zone_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def request_join_zone(zone_id, user_id):
    conn = get_connection()
    member_count = conn.execute(
        "SELECT COUNT(*) FROM zone_members WHERE zone_id=?", (zone_id,)
    ).fetchone()[0]
    zone = conn.execute("SELECT * FROM zones WHERE id=? AND status='active'", (zone_id,)).fetchone()
    if not zone:
        conn.close()
        return False, "Zone is no longer active."
    if member_count >= 10:
        conn.close()
        return False, "Zone is full (10 members max)."
    already = conn.execute(
        "SELECT id FROM zone_members WHERE zone_id=? AND user_id=?", (zone_id, user_id)
    ).fetchone()
    if already:
        conn.close()
        return True, "Already a member."
    conn.execute("INSERT OR IGNORE INTO zone_members (zone_id,user_id) VALUES (?,?)", (zone_id, user_id))
    # system message
    user = conn.execute("SELECT username FROM users WHERE id=?", (user_id,)).fetchone()
    conn.execute(
        "INSERT INTO zone_messages (zone_id,user_id,content,message_type) VALUES (?,?,?,?)",
        (zone_id, user_id, f"{user[0]} joined the Zone", "system")
    )
    conn.execute("UPDATE zones SET last_activity=CURRENT_TIMESTAMP WHERE id=?", (zone_id,))
    conn.commit()
    conn.close()
    return True, "Joined zone successfully!"


def send_zone_message(zone_id, user_id, content):
    conn = get_connection()
    conn.execute(
        "INSERT INTO zone_messages (zone_id,user_id,content) VALUES (?,?,?)",
        (zone_id, user_id, content)
    )
    conn.execute("UPDATE zones SET last_activity=CURRENT_TIMESTAMP WHERE id=?", (zone_id,))
    conn.commit()
    conn.close()


def get_zone_messages(zone_id, limit=100):
    conn = get_connection()
    rows = conn.execute(
        """SELECT zm.*, u.username, u.display_name, u.avatar_path
           FROM zone_messages zm JOIN users u ON zm.user_id=u.id
           WHERE zm.zone_id=?
           ORDER BY zm.created_at ASC LIMIT ?""",
        (zone_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_zone_members(zone_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT u.id, u.username, u.display_name, u.avatar_path, zm.joined_at
           FROM zone_members zm JOIN users u ON zm.user_id=u.id
           WHERE zm.zone_id=?""",
        (zone_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def end_zone(zone_id, user_id):
    conn = get_connection()
    conn.execute(
        "UPDATE zones SET status='ended', ended_at=CURRENT_TIMESTAMP WHERE id=? AND creator_id=?",
        (zone_id, user_id)
    )
    conn.commit()
    conn.close()


def check_zone_inactivity():
    """End zones inactive for 10+ minutes."""
    conn = get_connection()
    conn.execute(
        """UPDATE zones SET status='ended', ended_at=CURRENT_TIMESTAMP
           WHERE status='active'
             AND last_activity < DATETIME('now','-10 minutes')"""
    )
    conn.commit()
    conn.close()


def rate_zone(zone_id, user_id, rating):
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO zone_ratings (zone_id,user_id,rating) VALUES (?,?,?)", (zone_id, user_id, rating))
        avg = conn.execute("SELECT AVG(rating), COUNT(*) FROM zone_ratings WHERE zone_id=?", (zone_id,)).fetchone()
        conn.execute("UPDATE zones SET rating_avg=?, rating_count=? WHERE id=?", (avg[0], avg[1], zone_id))
        conn.commit()
    except Exception:
        pass
    conn.close()


def is_zone_member(zone_id, user_id):
    conn = get_connection()
    r = conn.execute("SELECT id FROM zone_members WHERE zone_id=? AND user_id=?", (zone_id, user_id)).fetchone()
    conn.close()
    return r is not None


# ─── Top Zone ─────────────────────────────────────────────────────────────────

def compute_top_zone(month, year):
    conn = get_connection()
    conn.execute("DELETE FROM top_zone_monthly WHERE month=? AND year=?", (month, year))
    cats = conn.execute("SELECT name FROM categories").fetchall()
    for cat in cats:
        cat_name = cat[0]
        rows = conn.execute(
            """SELECT p.id,
                      (p.likes_count + p.comments_count*2 + p.shares_count*3 + p.saves_count*2 + p.views_count/10) as score
               FROM posts p
               WHERE p.category=?
                 AND strftime('%m', p.created_at)=?
                 AND strftime('%Y', p.created_at)=?
               ORDER BY score DESC LIMIT 10""",
            (cat_name, f"{month:02d}", str(year))
        ).fetchall()
        for rank, row in enumerate(rows, 1):
            conn.execute(
                "INSERT INTO top_zone_monthly (post_id,category,rank,month,year,score) VALUES (?,?,?,?,?,?)",
                (row[0], cat_name, rank, month, year, row[1])
            )
    conn.commit()
    conn.close()


def get_top_zone(month, year, category=None):
    conn = get_connection()
    if category:
        rows = conn.execute(
            """SELECT tz.*, p.*, u.username, u.display_name, u.avatar_path, u.is_verified
               FROM top_zone_monthly tz
               JOIN posts p ON tz.post_id=p.id
               JOIN users u ON p.user_id=u.id
               WHERE tz.month=? AND tz.year=? AND tz.category=?
               ORDER BY tz.rank ASC""",
            (month, year, category)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT tz.*, p.*, u.username, u.display_name, u.avatar_path, u.is_verified
               FROM top_zone_monthly tz
               JOIN posts p ON tz.post_id=p.id
               JOIN users u ON p.user_id=u.id
               WHERE tz.month=? AND tz.year=?
               ORDER BY tz.category, tz.rank ASC""",
            (month, year)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_top_zone_categories(month, year):
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT category FROM top_zone_monthly WHERE month=? AND year=?",
        (month, year)
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


# ─── Notifications ────────────────────────────────────────────────────────────

def _create_notification_conn(conn, user_id, from_user_id, ntype, content, post_id=None, zone_id=None):
    conn.execute(
        "INSERT INTO notifications (user_id,from_user_id,type,content,post_id,zone_id) VALUES (?,?,?,?,?,?)",
        (user_id, from_user_id, ntype, content, post_id, zone_id)
    )


def get_notifications(user_id, limit=50):
    conn = get_connection()
    rows = conn.execute(
        """SELECT n.*, u.username, u.display_name, u.avatar_path
           FROM notifications n
           LEFT JOIN users u ON n.from_user_id=u.id
           WHERE n.user_id=?
           ORDER BY n.created_at DESC LIMIT ?""",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_notifications_read(user_id):
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_unread_notification_count(user_id):
    conn = get_connection()
    r = conn.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (user_id,)).fetchone()
    conn.close()
    return r[0]


# ─── Messages ────────────────────────────────────────────────────────────────

def send_message(sender_id, receiver_id, content):
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (sender_id,receiver_id,content) VALUES (?,?,?)",
        (sender_id, receiver_id, content)
    )
    conn.commit()
    conn.close()


def get_conversation(user1_id, user2_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.*, u.username, u.display_name, u.avatar_path
           FROM messages m JOIN users u ON m.sender_id=u.id
           WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?)
           ORDER BY m.created_at ASC""",
        (user1_id, user2_id, user2_id, user1_id)
    ).fetchall()
    conn.execute(
        "UPDATE messages SET is_read=1 WHERE sender_id=? AND receiver_id=?",
        (user2_id, user1_id)
    )
    conn.commit()
    conn.close()
    return [dict(r) for r in rows]


def get_conversations(user_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT u.id, u.username, u.display_name, u.avatar_path,
                  m.content as last_message, m.created_at,
                  SUM(CASE WHEN m.is_read=0 AND m.receiver_id=? THEN 1 ELSE 0 END) as unread
           FROM messages m
           JOIN users u ON (CASE WHEN m.sender_id=? THEN m.receiver_id ELSE m.sender_id END)=u.id
           WHERE m.sender_id=? OR m.receiver_id=?
           GROUP BY u.id
           ORDER BY m.created_at DESC""",
        (user_id, user_id, user_id, user_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Trending ─────────────────────────────────────────────────────────────────

def get_trending_hashtags(limit=20):
    conn = get_connection()
    rows = conn.execute(
        """SELECT hashtag, SUM(count) as total
           FROM hashtag_trending
           WHERE date >= DATE('now','-7 days')
           GROUP BY hashtag
           ORDER BY total DESC LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Analytics ────────────────────────────────────────────────────────────────

def get_user_analytics(user_id):
    conn = get_connection()
    stats = conn.execute(
        """SELECT
               COUNT(*) as post_count,
               SUM(likes_count) as total_likes,
               SUM(views_count) as total_views,
               SUM(comments_count) as total_comments,
               SUM(shares_count) as total_shares,
               SUM(saves_count) as total_saves
           FROM posts WHERE user_id=?""",
        (user_id,)
    ).fetchone()
    user = conn.execute(
        "SELECT followers_count, following_count FROM users WHERE id=?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(stats) if stats else {}, dict(user) if user else {}


# ─── Reports & Blocks ────────────────────────────────────────────────────────

def report_content(reporter_id, post_id=None, reported_user_id=None, reason=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO reports (reporter_id,post_id,reported_user_id,reason) VALUES (?,?,?,?)",
        (reporter_id, post_id, reported_user_id, reason)
    )
    conn.commit()
    conn.close()


def block_user(blocker_id, blocked_id):
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO blocks (blocker_id,blocked_id) VALUES (?,?)", (blocker_id, blocked_id))
    conn.commit()
    conn.close()
