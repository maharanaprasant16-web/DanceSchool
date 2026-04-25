import streamlit as st
import sqlite3
import hashlib
from datetime import date, datetime
import pandas as pd
from contextlib import contextmanager

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Natyashree School of Dance",
    layout="wide",
    page_icon="💃",
)

DB     = "dance_school.db"
DAYS   = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

ADMIN_PAGES  = ["🔔 Notices", "👩‍🎓 Students", "🎓 Classes", "📋 Attendance", "💰 Fees", "👤 Users", "🚪 Logout"]
PARENT_PAGES = ["🔔 Notices", "📋 Attendance", "💰 Fees", "🚪 Logout"]

PAGE_KEY_MAP = {
    "🔔 Notices":    "Notices",
    "👩‍🎓 Students":  "Students",
    "🎓 Classes":    "Classes",
    "📋 Attendance": "Attendance",
    "💰 Fees":       "Fees",
    "👤 Users":      "Users",
    "🚪 Logout":     "Logout",
}


# ─────────────────────────────────────────
# THEME + HIDE STREAMLIT CHROME + PWA
# ─────────────────────────────────────────
def apply_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,500&family=DM+Sans:wght@300;400;500&display=swap');

    /* ── Hide Streamlit chrome ── */
    [data-testid="stToolbar"], [data-testid="stDecoration"],
    header[data-testid="stHeader"] { visibility:hidden !important; height:0 !important; }
    [data-testid="manage-app-button"], .viewerBadge_container__r5tak,
    .viewerBadge_link__qRIco, #MainMenu { visibility:hidden !important; display:none !important; }
    footer, footer * { visibility:hidden !important; height:0 !important; }
    [class*="viewerBadge"],[class*="toolbar"],[class*="StatusWidget"] { display:none !important; }

    /* ── Palette ── */
    :root {
        --bg-page:     #f7f3ee;
        --bg-card:     #ffffff;
        --bg-subtle:   #f0ebe3;
        --sage:        #5a7a65;
        --sage-dark:   #3d5c47;
        --sage-light:  #d6e8da;
        --sage-pale:   #edf4ef;
        --terra:       #c0614a;
        --terra-light: #f2d5ce;
        --terra-pale:  #fdf0ed;
        --amber:       #d4a017;
        --amber-pale:  #fef9ec;
        --text-main:   #2d2a26;
        --text-muted:  #7a7269;
        --text-light:  #b0a898;
        --border:      #e2dbd0;
        --border-dark: #c8bfb2;
        --shadow-sm:   0 1px 4px rgba(90,80,60,0.08);
        --shadow-md:   0 4px 16px rgba(90,80,60,0.12);
    }

    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stApp"], .main, section[data-testid="stMain"] {
        background-color: var(--bg-page) !important;
        color: var(--text-main) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 300;
    }
    .block-container { padding-top: 1.5rem !important; }

    h1 {
        font-family: 'Playfair Display', serif !important;
        font-size: 2rem !important; font-weight: 700 !important;
        color: var(--sage-dark) !important;
        border-bottom: 2px solid var(--sage-light);
        padding-bottom: 0.5rem; margin-bottom: 1.4rem !important;
    }
    h2 { font-family:'Playfair Display',serif !important; color:var(--sage-dark) !important;
         font-weight:500 !important; font-size:1.35rem !important; }
    h3 { color:var(--text-main) !important; font-weight:500 !important; }

    /* Buttons */
    .stButton > button {
        background-color:var(--bg-card) !important; color:var(--sage-dark) !important;
        border:1.5px solid var(--sage) !important; border-radius:8px !important;
        font-family:'DM Sans',sans-serif !important; font-weight:500 !important;
        font-size:0.82rem !important; letter-spacing:0.04em !important;
        padding:0.4rem 1rem !important; transition:all 0.18s ease !important;
        box-shadow:var(--shadow-sm) !important;
    }
    .stButton > button:hover {
        background-color:var(--sage-pale) !important; border-color:var(--sage-dark) !important;
        transform:translateY(-1px) !important; box-shadow:var(--shadow-md) !important;
    }
    .stButton > button[kind="primary"] {
        background-color:var(--sage) !important; color:#fff !important;
        border-color:var(--sage-dark) !important;
    }
    .stButton > button[kind="primary"]:hover { background-color:var(--sage-dark) !important; }

    /* Inputs */
    .stTextInput > div > div > input, .stNumberInput > div > div > input,
    .stDateInput > div > div > input, textarea {
        background-color:var(--bg-card) !important; color:var(--text-main) !important;
        border:1.5px solid var(--border-dark) !important; border-radius:8px !important;
        font-family:'DM Sans',sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus, textarea:focus {
        border-color:var(--sage) !important;
        box-shadow:0 0 0 3px rgba(90,122,101,0.15) !important;
    }
    .stSelectbox > div > div {
        background-color:var(--bg-card) !important; border:1.5px solid var(--border-dark) !important;
        border-radius:8px !important; color:var(--text-main) !important;
    }

    /* Labels */
    label, .stSelectbox label, .stTextInput label,
    .stNumberInput label, .stDateInput label, .stRadio label {
        color:var(--text-muted) !important; font-size:0.74rem !important;
        font-weight:500 !important; letter-spacing:0.07em !important;
        text-transform:uppercase !important; font-family:'DM Sans',sans-serif !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background-color:var(--bg-card) !important; border:1px solid var(--border) !important;
        border-radius:10px !important; margin-bottom:0.5rem !important;
        box-shadow:var(--shadow-sm) !important;
    }
    [data-testid="stExpander"] summary {
        color:var(--text-main) !important; font-family:'DM Sans',sans-serif !important;
        font-size:0.92rem !important;
    }
    [data-testid="stExpander"] summary:hover {
        color:var(--sage-dark) !important; background-color:var(--sage-pale) !important;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background-color:var(--bg-card) !important; border:1px solid var(--border) !important;
        border-radius:10px !important; padding:1rem 1.1rem !important;
        box-shadow:var(--shadow-sm) !important; border-left:4px solid var(--sage) !important;
    }
    [data-testid="stMetricLabel"] {
        color:var(--text-muted) !important; font-size:0.7rem !important;
        text-transform:uppercase !important; letter-spacing:0.08em !important;
    }
    [data-testid="stMetricValue"] {
        color:var(--sage-dark) !important;
        font-family:'Playfair Display',serif !important; font-size:1.8rem !important;
    }

    [data-testid="stDataFrame"] {
        border:1px solid var(--border) !important; border-radius:10px !important;
        overflow:hidden !important; box-shadow:var(--shadow-sm) !important;
    }

    .stSuccess { background-color:var(--sage-pale) !important; border-left:4px solid var(--sage) !important;
                 color:var(--sage-dark) !important; border-radius:8px !important; }
    .stError   { background-color:var(--terra-pale) !important; border-left:4px solid var(--terra) !important;
                 border-radius:8px !important; }
    .stWarning { background-color:var(--amber-pale) !important; border-left:4px solid var(--amber) !important;
                 border-radius:8px !important; }
    .stInfo    { background-color:#edf3fb !important; border-left:4px solid #4a86c8 !important;
                 border-radius:8px !important; }

    hr { border-color:var(--border) !important; margin:0.8rem 0 !important; }

    /* Nav bar */
    .nav-wrap {
        background:var(--bg-card); border:1px solid var(--border);
        border-radius:12px; padding:0.4rem 0.5rem;
        margin-bottom:1.6rem; box-shadow:var(--shadow-md);
    }
    .nav-wrap .stButton > button {
        background:transparent !important; border:none !important;
        color:var(--text-muted) !important; font-size:0.76rem !important;
        letter-spacing:0.08em !important; box-shadow:none !important;
        padding:0.28rem 0.6rem !important; border-radius:7px !important;
    }
    .nav-wrap .stButton > button:hover {
        color:var(--sage-dark) !important; background:var(--sage-pale) !important;
        transform:none !important; box-shadow:none !important;
    }

    /* Page header */
    .page-hdr {
        display:flex; align-items:center; gap:0.6rem;
        margin-bottom:1.2rem; padding-bottom:0.7rem;
        border-bottom:1.5px solid var(--sage-light);
    }
    .page-hdr h2 { margin:0 !important; }

    /* Attendance badges */
    .att-present {
        display:inline-block; background:var(--sage-pale); color:var(--sage-dark);
        border:1px solid var(--sage-light); border-radius:20px;
        padding:3px 14px; font-size:0.8rem; font-weight:500;
        font-family:'DM Sans',sans-serif;
    }
    .att-absent {
        display:inline-block; background:var(--terra-pale); color:var(--terra);
        border:1px solid var(--terra-light); border-radius:20px;
        padding:3px 14px; font-size:0.8rem; font-weight:500;
        font-family:'DM Sans',sans-serif;
    }

    /* Notice cards */
    .notice-card {
        background:var(--bg-card); border:1px solid var(--border);
        border-left:4px solid var(--sage); border-radius:10px;
        padding:1rem 1.2rem; margin-bottom:0.7rem;
        box-shadow:var(--shadow-sm); position:relative;
    }
    .notice-card.priority-high   { border-left-color:var(--terra); }
    .notice-card.priority-medium { border-left-color:var(--amber); }
    .notice-card.notice-read     { opacity:0.65; background:var(--bg-subtle); }
    .notice-title { font-family:'Playfair Display',serif; font-size:1.05rem;
                    color:var(--text-main); font-weight:500; margin-bottom:0.25rem; }
    .notice-body  { font-size:0.88rem; color:var(--text-muted); line-height:1.55; }
    .notice-meta  { font-size:0.72rem; color:var(--text-light); margin-top:0.5rem;
                    letter-spacing:0.04em; }

    /* Unread dot on notice card */
    .unread-dot {
        display:inline-block; width:9px; height:9px;
        background:#e03a2f; border-radius:50%;
        margin-right:6px; vertical-align:middle;
        box-shadow:0 0 0 2px rgba(224,58,47,0.2);
    }

    /* Acknowledge button */
    .ack-btn .stButton > button {
        background:var(--sage-pale) !important; border-color:var(--sage) !important;
        color:var(--sage-dark) !important; font-size:0.75rem !important;
        padding:0.25rem 0.8rem !important; border-radius:20px !important;
    }

    /* Push permission banner */
    .push-banner {
        background:linear-gradient(135deg,#edf4ef,#f7f3ee);
        border:1px solid var(--sage-light); border-radius:10px;
        padding:0.8rem 1rem; margin-bottom:1rem;
        display:flex; align-items:center; gap:0.8rem;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width:6px; height:6px; }
    ::-webkit-scrollbar-track { background:var(--bg-page); }
    ::-webkit-scrollbar-thumb { background:var(--border-dark); border-radius:4px; }
    ::-webkit-scrollbar-thumb:hover { background:var(--sage); }

    .stRadio [data-testid="stHorizontalBlock"] label {
        text-transform:none !important; font-size:0.88rem !important;
        letter-spacing:0 !important; color:var(--text-main) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # PWA + push notification JS
    st.markdown("""
    <link rel="manifest" href="data:application/json;charset=utf-8,%7B%22name%22%3A%22Natyashree%20School%20of%20Dance%22%2C%22short_name%22%3A%22Natyashree%22%2C%22start_url%22%3A%22%2F%22%2C%22display%22%3A%22standalone%22%2C%22background_color%22%3A%22%23f7f3ee%22%2C%22theme_color%22%3A%225a7a65%22%2C%22icons%22%3A%5B%7B%22src%22%3A%22https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Ftwitter%2Ftwemoji%400d94d70%2Fassets%2F72x72%2F1f483.png%22%2C%22sizes%22%3A%2272x72%22%2C%22type%22%3A%22image%2Fpng%22%7D%5D%7D">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Natyashree">
    <meta name="theme-color" content="#5a7a65">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">

    <script>
    // ── Browser Push Notification helpers ──────────────────────────
    // Exposed globally so Streamlit components can call them.

    window.NSD = window.NSD || {};

    // Request notification permission from the browser
    window.NSD.requestPermission = async function() {
        if (!("Notification" in window)) return "unsupported";
        if (Notification.permission === "granted") return "granted";
        if (Notification.permission === "denied")  return "denied";
        const result = await Notification.requestPermission();
        return result;
    };

    // Fire a browser pop-up notification
    window.NSD.notify = function(title, body, priority) {
        if (Notification.permission !== "granted") return;
        const icons = { high: "🔴", medium: "🟡", normal: "🟢" };
        const icon  = "https://cdn.jsdelivr.net/gh/twitter/twemoji@0d94d70/assets/72x72/1f514.png";
        const tag   = "natyashree-notice-" + Date.now();
        const n = new Notification("💃 " + title, {
            body:    body,
            icon:    icon,
            badge:   icon,
            tag:     tag,
            renotify: true,
        });
        // Auto-close after 6 s
        setTimeout(() => n.close(), 6000);
    };

    // Called on page load — checks permission state, auto-requests once
    window.NSD.init = async function() {
        if (!("Notification" in window)) return;
        if (Notification.permission === "default") {
            // Wait for user gesture before asking (browsers require it)
            // We mark a flag so the Python side can show a button instead
            window.__nsd_permission__ = "needs_request";
        } else {
            window.__nsd_permission__ = Notification.permission;
        }
    };

    window.NSD.init();
    </script>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# PUSH NOTIFICATION TRIGGER (JS bridge)
# ─────────────────────────────────────────
def fire_browser_notification(title: str, body: str, priority: str = "normal"):
    """Inject JS to pop a browser notification immediately."""
    safe_title = title.replace("'", "\\'").replace("\n", " ")
    safe_body  = body.replace("'",  "\\'").replace("\n", " ")
    st.markdown(f"""
    <script>
    (function() {{
        if (typeof window.NSD !== 'undefined') {{
            window.NSD.notify('{safe_title}', '{safe_body}', '{priority}');
        }}
    }})();
    </script>
    """, unsafe_allow_html=True)


def push_permission_banner():
    """Show a one-time banner to request browser notification permission."""
    st.markdown("""
    <div class="push-banner">
        <span style="font-size:1.4rem">🔔</span>
        <div style="flex:1">
            <strong style="font-size:0.88rem;color:#3d5c47">Enable Push Notifications</strong><br>
            <span style="font-size:0.78rem;color:#7a7269">
                Get instant alerts when the school posts a new notice.
            </span>
        </div>
    </div>
    <script>
    (async function() {
        if (!("Notification" in window)) return;
        if (Notification.permission === "default") {
            await Notification.requestPermission();
        }
    })();
    </script>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────
@contextmanager
def get_conn():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def db_run(sql: str, params: tuple = ()) -> bool:
    try:
        with get_conn() as c:
            c.execute(sql, params)
        return True
    except sqlite3.Error as e:
        st.error(f"DB error: {e}")
        return False


def db_all(sql: str, params: tuple = ()) -> list:
    try:
        with get_conn() as c:
            rows = c.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        st.error(f"DB error: {e}")
        return []


def db_one(sql: str, params: tuple = ()):
    rows = db_all(sql, params)
    return rows[0] if rows else None


# ─────────────────────────────────────────
# DB INIT
# ─────────────────────────────────────────
def init_db():
    ddl = [
        """CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','parent')),
            student_id INTEGER REFERENCES students(id)
        )""",
        """CREATE TABLE IF NOT EXISTS classes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, day TEXT NOT NULL,
            time TEXT NOT NULL, instructor TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, age INTEGER NOT NULL,
            gender TEXT NOT NULL, class_id INTEGER REFERENCES classes(id),
            guardian TEXT, contact TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            class_id   INTEGER REFERENCES classes(id),
            date TEXT NOT NULL, status TEXT NOT NULL,
            UNIQUE(student_id, date)
        )""",
        """CREATE TABLE IF NOT EXISTS fees(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            month TEXT NOT NULL, amount REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('due','paid')),
            UNIQUE(student_id, month)
        )""",
        # ── Notices (broadcast) ──
        """CREATE TABLE IF NOT EXISTS notices(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            body       TEXT NOT NULL,
            priority   TEXT NOT NULL DEFAULT 'normal'
                       CHECK(priority IN ('normal','medium','high')),
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_active  INTEGER NOT NULL DEFAULT 1
        )""",
        # ── Per-user read receipts ──
        """CREATE TABLE IF NOT EXISTS notice_reads(
            notice_id  INTEGER NOT NULL REFERENCES notices(id),
            username   TEXT    NOT NULL,
            read_at    TEXT    NOT NULL,
            PRIMARY KEY (notice_id, username)
        )""",
    ]
    with get_conn() as c:
        for stmt in ddl:
            c.execute(stmt)
    if not db_one("SELECT 1 FROM users WHERE role='admin'"):
        db_run(
            "INSERT OR IGNORE INTO users(username,password_hash,role) VALUES(?,?,?)",
            ("admin", hash_pw("admin123"), "admin"),
        )


# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def authenticate(username: str, password: str):
    user = db_one("SELECT * FROM users WHERE username=?", (username,))
    if user and user["password_hash"] == hash_pw(password):
        return user
    return None


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def require_admin():
    if st.session_state.user.get("role") != "admin":
        st.warning("Access denied.")
        st.stop()


def page_header(icon: str, title: str):
    st.markdown(
        f'<div class="page-hdr">'
        f'<span style="font-size:1.5rem;line-height:1">{icon}</span>'
        f'<h2>{title}</h2></div>',
        unsafe_allow_html=True,
    )


def unread_count_for_user(username: str) -> int:
    """Active notices not yet acknowledged by this user."""
    row = db_one("""
        SELECT COUNT(*) AS cnt FROM notices n
        WHERE n.is_active = 1
          AND NOT EXISTS (
              SELECT 1 FROM notice_reads r
              WHERE r.notice_id = n.id AND r.username = ?
          )
    """, (username,))
    return row["cnt"] if row else 0


def mark_notice_read(notice_id: int, username: str):
    db_run(
        """INSERT OR IGNORE INTO notice_reads(notice_id, username, read_at)
           VALUES(?, ?, ?)""",
        (notice_id, username, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )


def is_notice_read(notice_id: int, username: str) -> bool:
    return bool(db_one(
        "SELECT 1 FROM notice_reads WHERE notice_id=? AND username=?",
        (notice_id, username),
    ))


# ─────────────────────────────────────────
# TOP NAV
# ─────────────────────────────────────────
def top_menu(role: str):
    pages      = ADMIN_PAGES if role == "admin" else PARENT_PAGES
    username   = st.session_state.user["username"]
    unread     = unread_count_for_user(username)

    st.markdown('<div class="nav-wrap">', unsafe_allow_html=True)
    cols = st.columns(len(pages))
    for col, page_label in zip(cols, pages):
        label = page_label
        if "Notices" in page_label and unread > 0:
            label = f"{page_label} ({unread})"
        if col.button(label, use_container_width=True, key=f"nav_{page_label}"):
            st.session_state.page = PAGE_KEY_MAP[page_label]
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────
# PAGE: LOGIN
# ─────────────────────────────────────────
def login_page():
    st.markdown("""
    <div style="text-align:center;margin-top:0.5rem;margin-bottom:2rem">
        <div style="font-family:'Playfair Display',serif;font-style:italic;
                    font-size:0.9rem;color:#7a7269;letter-spacing:0.1em">Welcome to</div>
        <div style="font-family:'Playfair Display',serif;font-size:2.1rem;
                    font-weight:700;color:#3d5c47;letter-spacing:0.02em;margin:0.15rem 0 0.1rem">
            Natyashree</div>
        <div style="font-family:'DM Sans',sans-serif;font-size:0.68rem;color:#b0a898;
                    letter-spacing:0.22em;text-transform:uppercase">
            School of Dance — Management Portal</div>
        <div style="width:36px;height:2px;background:#5a7a65;margin:0.9rem auto 0;border-radius:2px"></div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""
        <div style="background:#fff;border:1px solid #e2dbd0;border-top:4px solid #5a7a65;
                    border-radius:14px;padding:2rem 1.8rem;box-shadow:0 4px 16px rgba(90,80,60,0.12)">
        """, unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign In →", type="primary", use_container_width=True):
            user = authenticate(username, password)
            if user:
                st.session_state.user = user
                st.session_state.page = "Notices"
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown("""
        <div style="margin-top:1.2rem;padding-top:1rem;border-top:1px solid #e2dbd0;
                    text-align:center;font-size:0.72rem;color:#b0a898;line-height:1.6">
            📱 <strong style="color:#7a7269">Install as App</strong><br>
            Android: tap ⋮ → <em>Add to Home screen</em><br>
            iPhone: tap ⎙ → <em>Add to Home Screen</em>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────
# PAGE: NOTICES
# ─────────────────────────────────────────
def notices_page():
    page_header("🔔", "Notices")
    user     = st.session_state.user
    username = user["username"]

    # ── Push permission banner (shown to everyone once) ───────────
    push_permission_banner()

    # ── Admin: post new notice ────────────────────────────────────
    if user["role"] == "admin":
        with st.expander("📝  Post New Notice"):
            n_title    = st.text_input("Title", key="ntc_title",
                                       placeholder="e.g. Annual Day Rehearsal")
            n_body     = st.text_area("Message", key="ntc_body", height=100,
                                      placeholder="Type your message to parents here…")
            n_priority = st.selectbox(
                "Priority", ["normal", "medium", "high"], key="ntc_priority",
                format_func=lambda x: {"normal":"🟢 Normal","medium":"🟡 Medium","high":"🔴 High"}[x],
            )
            if st.button("📢  Post Notice", type="primary"):
                if not n_title.strip() or not n_body.strip():
                    st.warning("Title and message are required.")
                else:
                    ok = db_run(
                        "INSERT INTO notices(title,body,priority,created_by,created_at,is_active) VALUES(?,?,?,?,?,1)",
                        (n_title.strip(), n_body.strip(), n_priority,
                         username, datetime.now().strftime("%Y-%m-%d %H:%M")),
                    )
                    if ok:
                        # Fire browser push notification for the posting admin too
                        fire_browser_notification(n_title.strip(), n_body.strip(), n_priority)
                        st.success("✅ Notice posted to all parents.")
                        st.rerun()

    # ── Summary strip ─────────────────────────────────────────────
    total_active = db_one("SELECT COUNT(*) AS cnt FROM notices WHERE is_active=1")["cnt"]
    unread       = unread_count_for_user(username)

    if total_active:
        sm1, sm2, _ = st.columns([1, 1, 4])
        sm1.metric("Total Notices", total_active)
        sm2.metric("Unread",        unread)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Active notices ────────────────────────────────────────────
    notices = db_all("SELECT * FROM notices WHERE is_active=1 ORDER BY created_at DESC")
    if not notices:
        st.markdown("""
        <div style="text-align:center;padding:2.5rem 0;color:#b0a898">
            <div style="font-size:2rem;margin-bottom:0.5rem">🔔</div>
            <div style="font-size:0.9rem">No notices at the moment.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Fire browser push for any unread notices on page load (parent view)
    # so if the tab is open they get a pop-up on navigation
    if user["role"] == "parent":
        for n in notices:
            if not is_notice_read(n["id"], username):
                fire_browser_notification(n["title"], n["body"], n["priority"])
                break  # fire only for the newest unread, not spam all

    for n in notices:
        read       = is_notice_read(n["id"], username)
        pclass     = {"normal": "", "medium": " priority-medium", "high": " priority-high"}[n["priority"]]
        read_class = " notice-read" if read else ""
        plabel     = {"normal": "🟢 Normal", "medium": "🟡 Medium", "high": "🔴 High"}[n["priority"]]
        unread_dot = "" if read else '<span class="unread-dot"></span>'

        st.markdown(f"""
        <div class="notice-card{pclass}{read_class}">
            <div class="notice-title">{unread_dot}{n['title']}</div>
            <div class="notice-body">{n['body']}</div>
            <div class="notice-meta">
                {plabel} &nbsp;·&nbsp; Posted by <strong>{n['created_by']}</strong>
                &nbsp;·&nbsp; {n['created_at']}
                {"&nbsp;·&nbsp; ✅ <em>Acknowledged</em>" if read else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action row
        action_cols = st.columns([2, 2, 8] if user["role"] == "admin" else [2, 10])

        if not read:
            # Acknowledge button (all users)
            with action_cols[0]:
                st.markdown('<div class="ack-btn">', unsafe_allow_html=True)
                if st.button("✔ Acknowledge", key=f"ack_{n['id']}"):
                    mark_notice_read(n["id"], username)
                    st.success("Marked as read.")
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Already read — show timestamp
            read_row = db_one(
                "SELECT read_at FROM notice_reads WHERE notice_id=? AND username=?",
                (n["id"], username),
            )
            if read_row:
                st.markdown(
                    f'<span style="font-size:0.72rem;color:#b0a898;padding-left:0.2rem">'
                    f'✅ Acknowledged at {read_row["read_at"]}</span>',
                    unsafe_allow_html=True,
                )

        if user["role"] == "admin":
            admin_col_idx = 1 if not read else 0
            with action_cols[admin_col_idx if not read else 0]:
                pass  # spacer
            del_col = action_cols[1] if not read else action_cols[0]
            with del_col:
                bcols = st.columns(2)
                if bcols[0].button("🔕 Archive", key=f"ndeact_{n['id']}"):
                    db_run("UPDATE notices SET is_active=0 WHERE id=?", (n["id"],))
                    st.rerun()
                if bcols[1].button("🗑️ Delete",  key=f"ndel_{n['id']}"):
                    db_run("DELETE FROM notice_reads WHERE notice_id=?", (n["id"],))
                    db_run("DELETE FROM notices WHERE id=?", (n["id"],))
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

    # ── Admin: archived notices ───────────────────────────────────
    if user["role"] == "admin":
        archived = db_all("SELECT * FROM notices WHERE is_active=0 ORDER BY created_at DESC")
        if archived:
            with st.expander(f"📂  Archived Notices ({len(archived)})"):
                for n in archived:
                    readers = db_all(
                        "SELECT username, read_at FROM notice_reads WHERE notice_id=?", (n["id"],)
                    )
                    st.markdown(f"""
                    <div style="padding:0.6rem 0.8rem;border:1px solid #e2dbd0;border-radius:8px;
                                margin-bottom:0.4rem;background:#f7f3ee;opacity:0.75">
                        <span style="font-size:0.9rem;color:#7a7269;font-weight:500">{n['title']}</span>
                        <span style="font-size:0.72rem;color:#b0a898;margin-left:0.8rem">{n['created_at']}</span>
                        <br><span style="font-size:0.75rem;color:#b0a898">
                            👁 Read by {len(readers)} user(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    rc1, rc2, _ = st.columns([1, 1, 6])
                    if rc1.button("♻️ Restore", key=f"nrest_{n['id']}"):
                        db_run("UPDATE notices SET is_active=1 WHERE id=?", (n["id"],))
                        st.rerun()
                    if rc2.button("🗑️ Delete",  key=f"nardel_{n['id']}"):
                        db_run("DELETE FROM notice_reads WHERE notice_id=?", (n["id"],))
                        db_run("DELETE FROM notices WHERE id=?", (n["id"],))
                        st.rerun()

        # ── Admin: read-receipt dashboard ─────────────────────────
        with st.expander("📊  Read Receipt Dashboard"):
            all_notices = db_all("SELECT * FROM notices ORDER BY created_at DESC")
            if not all_notices:
                st.info("No notices yet.")
            else:
                for n in all_notices:
                    readers = db_all(
                        "SELECT username, read_at FROM notice_reads WHERE notice_id=? ORDER BY read_at",
                        (n["id"],),
                    )
                    all_parents = db_all("SELECT username FROM users WHERE role='parent'")
                    total_parents = len(all_parents)
                    read_names    = {r["username"] for r in readers}
                    unread_names  = [p["username"] for p in all_parents if p["username"] not in read_names]

                    pct = round((len(readers) / total_parents) * 100) if total_parents else 0
                    st.markdown(f"""
                    <div style="background:var(--bg-card);border:1px solid var(--border);
                                border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.6rem">
                        <strong style="font-size:0.92rem;color:#2d2a26">{n['title']}</strong>
                        <span style="font-size:0.72rem;color:#b0a898;margin-left:0.6rem">
                            {n['created_at']}  ·
                            {'🟢 Active' if n['is_active'] else '📂 Archived'}
                        </span>
                        <div style="margin-top:0.5rem;font-size:0.8rem;color:#5a7a65">
                            ✅ Read by {len(readers)}/{total_parents} parents ({pct}%)
                        </div>
                        {"<div style='font-size:0.75rem;color:#b0a898;margin-top:0.2rem'>⏳ Pending: " + ", ".join(unread_names) + "</div>" if unread_names else ""}
                    </div>
                    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# PAGE: STUDENTS
# ─────────────────────────────────────────
def students_page():
    require_admin()
    page_header("👩‍🎓", "Students")

    classes    = db_all("SELECT id, name FROM classes ORDER BY name")
    class_opts = {"— No Class —": None, **{c["name"]: c["id"] for c in classes}}

    with st.expander("➕  Add New Student"):
        c1, c2   = st.columns(2)
        name     = c1.text_input("Full Name",                       key="ns_name")
        age      = c2.number_input("Age", 3, 100,                   key="ns_age")
        gender   = c1.selectbox("Gender", ["Female","Male","Other"], key="ns_gen")
        cls_sel  = c2.selectbox("Class", list(class_opts),          key="ns_cls")
        guardian = c1.text_input("Guardian Name",                   key="ns_guard")
        contact  = c2.text_input("Contact Number",                  key="ns_cont")
        if st.button("Add Student", type="primary"):
            if not name.strip():
                st.warning("Name is required.")
            else:
                ok = db_run(
                    "INSERT INTO students(name,age,gender,class_id,guardian,contact) VALUES(?,?,?,?,?,?)",
                    (name.strip(), age, gender, class_opts[cls_sel], guardian, contact),
                )
                if ok:
                    st.success(f"✅ '{name}' added.")
                    st.rerun()

    students = db_all("""
        SELECT s.*, c.name AS class_name
        FROM students s LEFT JOIN classes c ON s.class_id=c.id ORDER BY s.name
    """)
    if not students:
        st.info("No students enrolled yet.")
        return

    for s in students:
        cls_label = s.get("class_name") or "No class"
        with st.expander(f"{s['name']}  ·  {cls_label}  ·  Age {s['age']}"):
            c1, c2   = st.columns(2)
            gen_opts = ["Female","Male","Other"]
            new_name  = c1.text_input("Name",        s["name"],  key=f"sn{s['id']}")
            new_age   = c2.number_input("Age",3,100,  s["age"],  key=f"sa{s['id']}")
            new_gen   = c1.selectbox("Gender", gen_opts,
                                     index=gen_opts.index(s["gender"]) if s["gender"] in gen_opts else 0,
                                     key=f"sg{s['id']}")
            cls_keys = list(class_opts)
            curr_idx = list(class_opts.values()).index(s["class_id"]) if s["class_id"] in class_opts.values() else 0
            new_cls   = c2.selectbox("Class", cls_keys, index=curr_idx, key=f"sc{s['id']}")
            new_guard = c1.text_input("Guardian", s.get("guardian") or "", key=f"sgu{s['id']}")
            new_cont  = c2.text_input("Contact",  s.get("contact")  or "", key=f"sco{s['id']}")
            b1, b2 = st.columns(2)
            if b1.button("💾 Update", key=f"su{s['id']}"):
                db_run(
                    "UPDATE students SET name=?,age=?,gender=?,class_id=?,guardian=?,contact=? WHERE id=?",
                    (new_name, new_age, new_gen, class_opts[new_cls], new_guard, new_cont, s["id"]),
                )
                st.success("Updated ✅"); st.rerun()
            if b2.button("🗑️ Delete", key=f"sd{s['id']}"):
                db_run("DELETE FROM students WHERE id=?", (s["id"],))
                st.warning(f"'{s['name']}' removed."); st.rerun()


# ─────────────────────────────────────────
# PAGE: CLASSES
# ─────────────────────────────────────────
def classes_page():
    require_admin()
    page_header("🎓", "Classes")

    with st.expander("➕  Add New Class"):
        c1, c2     = st.columns(2)
        name       = c1.text_input("Class Name",           key="nc_name")
        instructor = c2.text_input("Instructor",           key="nc_inst")
        day        = c1.selectbox("Day", DAYS,             key="nc_day")
        time_val   = c2.text_input("Time (e.g. 5:00 PM)", key="nc_time")
        if st.button("Add Class", type="primary"):
            if not name.strip():
                st.warning("Class name is required.")
            else:
                ok = db_run("INSERT INTO classes(name,day,time,instructor) VALUES(?,?,?,?)",
                            (name.strip(), day, time_val, instructor))
                if ok:
                    st.success(f"✅ Class '{name}' added."); st.rerun()

    classes = db_all("SELECT * FROM classes ORDER BY day, time")
    if not classes:
        st.info("No classes created yet."); return

    for cls in classes:
        with st.expander(f"{cls['name']}  ·  {cls['day']}  {cls['time']}  ·  {cls['instructor']}"):
            c1, c2   = st.columns(2)
            new_name = c1.text_input("Name",        cls["name"],       key=f"cn{cls['id']}")
            new_inst = c2.text_input("Instructor",   cls["instructor"], key=f"ci{cls['id']}")
            new_day  = c1.selectbox("Day", DAYS,
                                    index=DAYS.index(cls["day"]) if cls["day"] in DAYS else 0,
                                    key=f"cd{cls['id']}")
            new_time = c2.text_input("Time", cls["time"], key=f"ct{cls['id']}")
            b1, b2 = st.columns(2)
            if b1.button("💾 Update", key=f"cu{cls['id']}"):
                db_run("UPDATE classes SET name=?,day=?,time=?,instructor=? WHERE id=?",
                       (new_name, new_day, new_time, new_inst, cls["id"]))
                st.success("Updated ✅"); st.rerun()
            if b2.button("🗑️ Delete", key=f"cdel{cls['id']}"):
                db_run("DELETE FROM classes WHERE id=?", (cls["id"],))
                st.warning(f"Class '{cls['name']}' deleted."); st.rerun()


# ─────────────────────────────────────────
# PAGE: ATTENDANCE
# ─────────────────────────────────────────
def attendance_page():
    page_header("📋", "Attendance")
    today = date.today().isoformat()
    user  = st.session_state.user

    # ── PARENT: read-only ─────────────────────────────────────────
    if user["role"] == "parent":
        student_id = user.get("student_id")
        if not student_id:
            st.info("No student linked. Contact the school admin.")
            return
        student = db_one("SELECT * FROM students WHERE id=?", (student_id,))
        if not student:
            st.info("Linked student not found."); return

        st.markdown(
            f'<p style="font-size:0.85rem;color:#7a7269;margin-bottom:0.5rem">'
            f'Attendance record for <strong style="color:#3d5c47">{student["name"]}</strong></p>',
            unsafe_allow_html=True,
        )
        cf, ct, _ = st.columns([1, 1, 2])
        date_from = cf.date_input("From", value=date.today().replace(day=1))
        date_to   = ct.date_input("To",   value=date.today())

        records = db_all(
            "SELECT date, status FROM attendance WHERE student_id=? AND date BETWEEN ? AND ? ORDER BY date DESC",
            (student_id, date_from.isoformat(), date_to.isoformat()),
        )
        if not records:
            st.info("No records found for the selected date range."); return

        total   = len(records)
        present = sum(1 for r in records if r["status"] == "Present")
        absent  = total - present
        pct     = round((present / total) * 100) if total else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Classes", total)
        m2.metric("Present",  present)
        m3.metric("Absent",   absent)
        m4.metric("Attendance %", f"{pct}%")
        st.markdown("<br>", unsafe_allow_html=True)

        hc1, hc2 = st.columns([2, 2])
        hc1.markdown('<span style="font-size:0.72rem;color:#7a7269;letter-spacing:0.12em;font-weight:500;text-transform:uppercase">Date</span>', unsafe_allow_html=True)
        hc2.markdown('<span style="font-size:0.72rem;color:#7a7269;letter-spacing:0.12em;font-weight:500;text-transform:uppercase">Status</span>', unsafe_allow_html=True)
        st.markdown('<div style="border-top:1px solid #e2dbd0;margin-bottom:0.4rem"></div>', unsafe_allow_html=True)

        for r in records:
            rc1, rc2 = st.columns([2, 2])
            rc1.markdown(f'<span style="font-size:0.9rem;color:#2d2a26">{r["date"]}</span>', unsafe_allow_html=True)
            badge = "att-present" if r["status"] == "Present" else "att-absent"
            rc2.markdown(f'<span class="{badge}">{r["status"]}</span>', unsafe_allow_html=True)
        return

    # ── ADMIN: editable ───────────────────────────────────────────
    chosen_date = st.date_input("Date", value=date.today()).isoformat()
    classes  = db_all("SELECT * FROM classes ORDER BY name")
    cls_opts = {"All Classes": None, **{c["name"]: c["id"] for c in classes}}
    filter_cls      = st.selectbox("Filter by Class", list(cls_opts))
    selected_cls_id = cls_opts[filter_cls]

    if selected_cls_id:
        students = db_all("SELECT * FROM students WHERE class_id=? ORDER BY name", (selected_cls_id,))
    else:
        students = db_all("SELECT * FROM students WHERE class_id IS NOT NULL ORDER BY name")

    if not students:
        st.info("No students found for the selected filter."); return

    existing = {
        r["student_id"]: r["status"]
        for r in db_all("SELECT student_id, status FROM attendance WHERE date=?", (chosen_date,))
    }

    st.markdown("<br>", unsafe_allow_html=True)
    hdr = st.columns([4, 3, 2])
    hdr[0].markdown('<span style="font-size:0.72rem;color:#7a7269;letter-spacing:0.12em;font-weight:500;text-transform:uppercase">Student</span>', unsafe_allow_html=True)
    hdr[1].markdown('<span style="font-size:0.72rem;color:#7a7269;letter-spacing:0.12em;font-weight:500;text-transform:uppercase">Status</span>', unsafe_allow_html=True)
    hdr[2].markdown('<span style="font-size:0.72rem;color:#7a7269;letter-spacing:0.12em;font-weight:500;text-transform:uppercase">Save</span>', unsafe_allow_html=True)
    st.markdown('<div style="border-top:1px solid #e2dbd0;margin-bottom:0.4rem"></div>', unsafe_allow_html=True)

    for s in students:
        c1, c2, c3 = st.columns([4, 3, 2])
        c1.write(s["name"])
        current = existing.get(s["id"], "Present")
        status  = c2.radio("", ["Present", "Absent"],
                           index=0 if current == "Present" else 1,
                           horizontal=True,
                           key=f"att_{s['id']}_{chosen_date}",
                           label_visibility="collapsed")
        if c3.button("Save", key=f"asave_{s['id']}_{chosen_date}"):
            db_run(
                """INSERT INTO attendance(student_id,class_id,date,status) VALUES(?,?,?,?)
                   ON CONFLICT(student_id,date) DO UPDATE SET status=excluded.status""",
                (s["id"], s.get("class_id"), chosen_date, status),
            )
            st.success(f"Saved: {s['name']} → {status}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾  Save All Attendance", type="primary"):
        for s in students:
            status = st.session_state.get(f"att_{s['id']}_{chosen_date}", "Present")
            db_run(
                """INSERT INTO attendance(student_id,class_id,date,status) VALUES(?,?,?,?)
                   ON CONFLICT(student_id,date) DO UPDATE SET status=excluded.status""",
                (s["id"], s.get("class_id"), chosen_date, status),
            )
        st.success("✅ All attendance records saved.")


# ─────────────────────────────────────────
# PAGE: FEES
# ─────────────────────────────────────────
def fees_page():
    page_header("💰", "Fees")
    user = st.session_state.user

    if user["role"] == "parent" and user.get("student_id"):
        students = db_all("SELECT * FROM students WHERE id=?", (user["student_id"],))
    else:
        students = db_all("SELECT * FROM students ORDER BY name")

    if not students:
        st.info("No students found."); return

    smap = {s["name"]: s["id"] for s in students}

    if user["role"] == "admin":
        with st.expander("➕  Record Fee Payment"):
            c1, c2, c3, c4 = st.columns(4)
            sel_stu = c1.selectbox("Student", list(smap), key="fee_stu")
            month   = c2.selectbox("Month",   MONTHS,     key="fee_mon")
            amount  = c3.number_input("Amount (₹)", min_value=0.0, step=100.0, key="fee_amt")
            status  = c4.selectbox("Status", ["due","paid"], key="fee_sta")
            if st.button("Save Fee Record", type="primary"):
                ok = db_run(
                    """INSERT INTO fees(student_id,month,amount,status) VALUES(?,?,?,?)
                       ON CONFLICT(student_id,month) DO UPDATE SET amount=excluded.amount,status=excluded.status""",
                    (smap[sel_stu], month, amount, status),
                )
                if ok:
                    st.success("Fee record saved ✅"); st.rerun()

    ids          = list(smap.values())
    placeholders = ",".join("?" * len(ids))
    rows = db_all(
        f"""SELECT f.id, s.name AS Student, f.month AS Month,
                   f.amount AS Amount, f.status AS Status
            FROM fees f JOIN students s ON f.student_id=s.id
            WHERE f.student_id IN ({placeholders})
            ORDER BY s.name, f.month""",
        tuple(ids),
    )
    if rows:
        df = pd.DataFrame(rows)
        def color_status(val):
            if val == "paid":
                return "background-color:#edf4ef;color:#3d5c47;font-weight:500"
            return "background-color:#fdf0ed;color:#c0614a;font-weight:500"
        st.dataframe(
            df.drop(columns=["id"]).style.map(color_status, subset=["Status"]),
            use_container_width=True,
        )
        total_paid = sum(r["Amount"] for r in rows if r["Status"] == "paid")
        total_due  = sum(r["Amount"] for r in rows if r["Status"] == "due")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Paid ✅",    f"₹{total_paid:,.0f}")
        m2.metric("Total Pending ⚠️", f"₹{total_due:,.0f}")
        m3.metric("Total Students",   len(smap))
    else:
        st.info("No fee records found.")


# ─────────────────────────────────────────
# PAGE: USERS
# ─────────────────────────────────────────
def users_page():
    require_admin()
    page_header("👤", "Users")

    students = db_all("SELECT id, name FROM students ORDER BY name")
    smap = {"— None —": None, **{s["name"]: s["id"] for s in students}}

    with st.expander("➕  Create New User"):
        c1, c2   = st.columns(2)
        username = c1.text_input("Username",  key="nu_user")
        password = c2.text_input("Password", type="password", key="nu_pw")
        role     = c1.selectbox("Role", ["parent","admin"], key="nu_role")
        linked   = c2.selectbox("Link to Student", list(smap), key="nu_stu")
        if st.button("Create User", type="primary"):
            if not username.strip() or not password:
                st.warning("Username and password are required.")
            elif db_one("SELECT 1 FROM users WHERE username=?", (username,)):
                st.error("Username already exists.")
            else:
                ok = db_run(
                    "INSERT INTO users(username,password_hash,role,student_id) VALUES(?,?,?,?)",
                    (username.strip(), hash_pw(password), role, smap[linked]),
                )
                if ok:
                    st.success(f"User '{username}' created ✅"); st.rerun()

    users = db_all("SELECT id, username, role, student_id FROM users ORDER BY role, username")
    if users:
        st.dataframe(pd.DataFrame(users), use_container_width=True)

    with st.expander("🔑  Change Password"):
        unames = [u["username"] for u in users]
        target = st.selectbox("Select User", unames, key="cpw_user")
        new_pw = st.text_input("New Password", type="password", key="cpw_pw")
        if st.button("Update Password"):
            if not new_pw:
                st.warning("Password cannot be empty.")
            else:
                db_run("UPDATE users SET password_hash=? WHERE username=?", (hash_pw(new_pw), target))
                st.success("Password updated ✅")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    init_db()
    apply_theme()

    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "Notices")

    st.markdown(
        '<h1 style="text-align:center;letter-spacing:0.03em">✦ Natyashree School of Dance ✦</h1>',
        unsafe_allow_html=True,
    )

    if not st.session_state.user:
        login_page()
        return

    top_menu(st.session_state.user["role"])

    page = st.session_state.page
    if   page == "Notices":    notices_page()
    elif page == "Students":   students_page()
    elif page == "Classes":    classes_page()
    elif page == "Attendance": attendance_page()
    elif page == "Fees":       fees_page()
    elif page == "Users":      users_page()
    elif page == "Logout":
        st.session_state.user = None
        st.session_state.page = "Notices"
        st.rerun()


if __name__ == "__main__":
    main()
