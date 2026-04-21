import streamlit as st
import sqlite3
import hashlib
from datetime import date
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

ADMIN_PAGES  = ["Students", "Classes", "Attendance", "Fees", "Users", "Logout"]
PARENT_PAGES = ["Attendance", "Fees", "Logout"]

#----------------Hide streamlit buttons 

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display: none;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# ─────────────────────────────────────────
# THEME  — soft sage + ivory + terracotta
# ─────────────────────────────────────────
def apply_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,500&family=DM+Sans:wght@300;400;500&display=swap');

    :root {
        --bg-page:     #f7f3ee;
        --bg-card:     #ffffff;
        --bg-subtle:   #f0ebe3;
        --bg-hover:    #ede6db;
        --sage:        #5a7a65;
        --sage-dark:   #3d5c47;
        --sage-light:  #d6e8da;
        --sage-pale:   #edf4ef;
        --terra:       #c0614a;
        --terra-light: #f2d5ce;
        --terra-pale:  #fdf0ed;
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

    /* Remove default streamlit top padding */
    .block-container { padding-top: 2rem !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: var(--bg-card) !important;
        border-right: 1px solid var(--border);
    }

    /* ── Headings ── */
    h1 {
        font-family: 'Playfair Display', serif !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: var(--sage-dark) !important;
        letter-spacing: 0.01em;
        border-bottom: 2px solid var(--sage-light);
        padding-bottom: 0.6rem;
        margin-bottom: 1.6rem !important;
    }
    h2 {
        font-family: 'Playfair Display', serif !important;
        color: var(--sage-dark) !important;
        font-weight: 500 !important;
        font-size: 1.4rem !important;
        letter-spacing: 0.01em;
    }
    h3 {
        font-family: 'DM Sans', sans-serif !important;
        color: var(--text-main) !important;
        font-weight: 500 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background-color: var(--bg-card) !important;
        color: var(--sage-dark) !important;
        border: 1.5px solid var(--sage) !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.83rem !important;
        letter-spacing: 0.04em !important;
        padding: 0.42rem 1.1rem !important;
        transition: all 0.18s ease !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .stButton > button:hover {
        background-color: var(--sage-pale) !important;
        border-color: var(--sage-dark) !important;
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"] {
        background-color: var(--sage) !important;
        color: #ffffff !important;
        border-color: var(--sage-dark) !important;
        font-weight: 500 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: var(--sage-dark) !important;
        border-color: var(--sage-dark) !important;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    textarea {
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
        border: 1.5px solid var(--border-dark) !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.9rem !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--sage) !important;
        box-shadow: 0 0 0 3px rgba(90,122,101,0.15) !important;
    }
    .stSelectbox > div > div {
        background-color: var(--bg-card) !important;
        border: 1.5px solid var(--border-dark) !important;
        border-radius: 8px !important;
        color: var(--text-main) !important;
    }

    /* ── Labels ── */
    label, .stSelectbox label, .stTextInput label,
    .stNumberInput label, .stDateInput label, .stRadio label {
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.07em !important;
        text-transform: uppercase !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    /* ── Expanders ── */
    [data-testid="stExpander"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        margin-bottom: 0.5rem !important;
        box-shadow: var(--shadow-sm) !important;
    }
    [data-testid="stExpander"] summary {
        color: var(--text-main) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 400 !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stExpander"] summary:hover {
        color: var(--sage-dark) !important;
        background-color: var(--sage-pale) !important;
    }
    [data-testid="stExpander"] > div > div {
        background-color: var(--bg-subtle) !important;
        border-top: 1px solid var(--border) !important;
        padding: 1rem !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 1rem 1.2rem !important;
        box-shadow: var(--shadow-sm) !important;
        border-left: 4px solid var(--sage) !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.72rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--sage-dark) !important;
        font-family: 'Playfair Display', serif !important;
        font-size: 1.9rem !important;
    }

    /* ── Dataframes ── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* ── Alerts ── */
    [data-testid="stNotification"],
    div[data-baseweb="notification"] {
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stSuccess { background-color: var(--sage-pale) !important; border-left: 4px solid var(--sage) !important; color: var(--sage-dark) !important; }
    .stError   { background-color: var(--terra-pale) !important; border-left: 4px solid var(--terra) !important; }
    .stWarning { background-color: #fef9ec !important; border-left: 4px solid #d4a017 !important; }
    .stInfo    { background-color: #edf3fb !important; border-left: 4px solid #4a86c8 !important; }

    /* ── Divider ── */
    hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

    /* ── Nav bar ── */
    .nav-wrap {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.4rem 0.5rem;
        margin-bottom: 1.8rem;
        box-shadow: var(--shadow-md);
    }
    .nav-wrap .stButton > button {
        background: transparent !important;
        border: none !important;
        color: var(--text-muted) !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.1em !important;
        box-shadow: none !important;
        padding: 0.3rem 0.8rem !important;
        border-radius: 7px !important;
    }
    .nav-wrap .stButton > button:hover {
        color: var(--sage-dark) !important;
        background: var(--sage-pale) !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* ── Page header ── */
    .page-hdr {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 1.4rem;
        padding-bottom: 0.8rem;
        border-bottom: 1.5px solid var(--sage-light);
    }
    .page-hdr h2 { margin: 0 !important; }

    /* ── Attendance read-only badge ── */
    .att-badge-present {
        display: inline-block;
        background: var(--sage-pale);
        color: var(--sage-dark);
        border: 1px solid var(--sage-light);
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 0.8rem;
        font-weight: 500;
        font-family: 'DM Sans', sans-serif;
    }
    .att-badge-absent {
        display: inline-block;
        background: var(--terra-pale);
        color: var(--terra);
        border: 1px solid var(--terra-light);
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 0.8rem;
        font-weight: 500;
        font-family: 'DM Sans', sans-serif;
    }
    .att-badge-none {
        display: inline-block;
        background: #f5f5f5;
        color: var(--text-light);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 0.8rem;
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Login card ── */
    .login-wrap {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        box-shadow: var(--shadow-md);
        max-width: 420px;
        margin: 2rem auto;
        border-top: 4px solid var(--sage);
    }

    /* ── Radio ── */
    .stRadio [data-testid="stHorizontalBlock"] label {
        text-transform: none !important;
        font-size: 0.88rem !important;
        letter-spacing: 0 !important;
        color: var(--text-main) !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-page); }
    ::-webkit-scrollbar-thumb { background: var(--border-dark); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--sage); }
    </style>
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
            name TEXT NOT NULL,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            instructor TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            class_id INTEGER REFERENCES classes(id),
            guardian TEXT,
            contact TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            class_id INTEGER REFERENCES classes(id),
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(student_id, date)
        )""",
        """CREATE TABLE IF NOT EXISTS fees(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            month TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('due','paid')),
            UNIQUE(student_id, month)
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
def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


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
        f'<div class="page-hdr"><span style="font-size:1.6rem;line-height:1">{icon}</span>'
        f'<h2>{title}</h2></div>',
        unsafe_allow_html=True,
    )


def is_admin() -> bool:
    return st.session_state.user.get("role") == "admin"


# ─────────────────────────────────────────
# TOP NAV
# ─────────────────────────────────────────
def top_menu(role: str):
    pages = ADMIN_PAGES if role == "admin" else PARENT_PAGES
    st.markdown('<div class="nav-wrap">', unsafe_allow_html=True)
    cols = st.columns(len(pages))
    for col, page in zip(cols, pages):
        if col.button(page, use_container_width=True, key=f"nav_{page}"):
            st.session_state.page = page
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────
# PAGE: LOGIN
# ─────────────────────────────────────────
def login_page():
    st.markdown("""
    <div style="text-align:center;margin-top:1rem;margin-bottom:2.5rem">
        <div style="font-family:'Playfair Display',serif;font-style:italic;
                    font-size:0.95rem;color:#7a7269;letter-spacing:0.1em">
            Welcome to</div>
        <div style="font-family:'Playfair Display',serif;font-size:2.2rem;
                    font-weight:700;color:#3d5c47;letter-spacing:0.02em;
                    margin:0.2rem 0 0.1rem">
            Natyashree</div>
        <div style="font-family:'DM Sans',sans-serif;font-size:0.7rem;
                    color:#b0a898;letter-spacing:0.22em;text-transform:uppercase">
            School of Dance — Management Portal</div>
        <div style="width:40px;height:2px;background:#5a7a65;margin:1rem auto 0;border-radius:2px"></div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign In →", type="primary", use_container_width=True):
            user = authenticate(username, password)
            if user:
                st.session_state.user = user
                st.session_state.page = "Students" if user["role"] == "admin" else "Attendance"
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown("</div>", unsafe_allow_html=True)


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
        name     = c1.text_input("Full Name",                key="ns_name")
        age      = c2.number_input("Age", 3, 100,           key="ns_age")
        gender   = c1.selectbox("Gender", ["Female","Male","Other"], key="ns_gen")
        cls_sel  = c2.selectbox("Class", list(class_opts),  key="ns_cls")
        guardian = c1.text_input("Guardian Name",            key="ns_guard")
        contact  = c2.text_input("Contact Number",           key="ns_cont")
        if st.button("Add Student", type="primary"):
            if not name.strip():
                st.warning("Name is required.")
            else:
                ok = db_run(
                    "INSERT INTO students(name,age,gender,class_id,guardian,contact) VALUES(?,?,?,?,?,?)",
                    (name.strip(), age, gender, class_opts[cls_sel], guardian, contact),
                )
                if ok:
                    st.success(f"✅  '{name}' added.")
                    st.rerun()

    students = db_all("""
        SELECT s.*, c.name AS class_name
        FROM students s LEFT JOIN classes c ON s.class_id = c.id
        ORDER BY s.name
    """)
    if not students:
        st.info("No students enrolled yet.")
        return

    for s in students:
        cls_label = s.get("class_name") or "No class"
        with st.expander(f"{s['name']}  ·  {cls_label}  ·  Age {s['age']}"):
            c1, c2   = st.columns(2)
            gen_opts = ["Female", "Male", "Other"]
            new_name  = c1.text_input("Name",      s["name"],  key=f"sn{s['id']}")
            new_age   = c2.number_input("Age",3,100,s["age"],  key=f"sa{s['id']}")
            new_gen   = c1.selectbox("Gender", gen_opts,
                                     index=gen_opts.index(s["gender"]) if s["gender"] in gen_opts else 0,
                                     key=f"sg{s['id']}")
            cls_keys  = list(class_opts)
            curr_idx  = list(class_opts.values()).index(s["class_id"]) if s["class_id"] in class_opts.values() else 0
            new_cls   = c2.selectbox("Class", cls_keys, index=curr_idx, key=f"sc{s['id']}")
            new_guard = c1.text_input("Guardian", s.get("guardian") or "", key=f"sgu{s['id']}")
            new_cont  = c2.text_input("Contact",  s.get("contact")  or "", key=f"sco{s['id']}")
            b1, b2    = st.columns(2)
            if b1.button("💾  Update", key=f"su{s['id']}"):
                db_run(
                    "UPDATE students SET name=?,age=?,gender=?,class_id=?,guardian=?,contact=? WHERE id=?",
                    (new_name, new_age, new_gen, class_opts[new_cls], new_guard, new_cont, s["id"]),
                )
                st.success("Updated ✅")
                st.rerun()
            if b2.button("🗑️  Delete", key=f"sd{s['id']}"):
                db_run("DELETE FROM students WHERE id=?", (s["id"],))
                st.warning(f"'{s['name']}' removed.")
                st.rerun()


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
                ok = db_run(
                    "INSERT INTO classes(name,day,time,instructor) VALUES(?,?,?,?)",
                    (name.strip(), day, time_val, instructor),
                )
                if ok:
                    st.success(f"✅  Class '{name}' added.")
                    st.rerun()

    classes = db_all("SELECT * FROM classes ORDER BY day, time")
    if not classes:
        st.info("No classes created yet.")
        return

    for cls in classes:
        with st.expander(f"{cls['name']}  ·  {cls['day']}  {cls['time']}  ·  {cls['instructor']}"):
            c1, c2   = st.columns(2)
            new_name = c1.text_input("Name",       cls["name"],       key=f"cn{cls['id']}")
            new_inst = c2.text_input("Instructor",  cls["instructor"], key=f"ci{cls['id']}")
            new_day  = c1.selectbox("Day", DAYS,
                                    index=DAYS.index(cls["day"]) if cls["day"] in DAYS else 0,
                                    key=f"cd{cls['id']}")
            new_time = c2.text_input("Time", cls["time"], key=f"ct{cls['id']}")
            b1, b2   = st.columns(2)
            if b1.button("💾  Update", key=f"cu{cls['id']}"):
                db_run(
                    "UPDATE classes SET name=?,day=?,time=?,instructor=? WHERE id=?",
                    (new_name, new_day, new_time, new_inst, cls["id"]),
                )
                st.success("Updated ✅")
                st.rerun()
            if b2.button("🗑️  Delete", key=f"cdel{cls['id']}"):
                db_run("DELETE FROM classes WHERE id=?", (cls["id"],))
                st.warning(f"Class '{cls['name']}' deleted.")
                st.rerun()


# ─────────────────────────────────────────
# PAGE: ATTENDANCE
# Two modes:
#   admin  → editable (radio + save buttons)
#   parent → read-only display (badges only, for their child)
# ─────────────────────────────────────────
def attendance_page():
    page_header("📋", "Attendance")
    today = date.today().isoformat()
    user  = st.session_state.user

    # ── PARENT VIEW  (read-only) ───────────────────────────────────
    if user["role"] == "parent":
        student_id = user.get("student_id")
        if not student_id:
            st.info("No student is linked to your account. Please contact the school admin.")
            return

        student = db_one("SELECT * FROM students WHERE id=?", (student_id,))
        if not student:
            st.info("Linked student not found.")
            return

        # Date range selector (view only)
        st.markdown(
            f'<p style="font-size:0.85rem;color:#7a7269;margin-bottom:0.5rem">'
            f'Viewing attendance for <strong style="color:#3d5c47">{student["name"]}</strong></p>',
            unsafe_allow_html=True,
        )
        col_from, col_to, _ = st.columns([1, 1, 2])
        date_from = col_from.date_input("From", value=date.today().replace(day=1))
        date_to   = col_to.date_input("To",   value=date.today())

        records = db_all(
            "SELECT date, status FROM attendance WHERE student_id=? AND date BETWEEN ? AND ? ORDER BY date DESC",
            (student_id, date_from.isoformat(), date_to.isoformat()),
        )

        if not records:
            st.info("No attendance records found for the selected date range.")
            return

        # Summary strip
        total    = len(records)
        present  = sum(1 for r in records if r["status"] == "Present")
        absent   = total - present
        pct      = round((present / total) * 100) if total else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Classes", total)
        m2.metric("Present", present)
        m3.metric("Absent", absent)
        m4.metric("Attendance %", f"{pct}%")

        st.markdown("<br>", unsafe_allow_html=True)

        # Table header
        hdr = st.columns([2, 2])
        hdr[0].markdown('<span style="font-size:0.72rem;color:#7a7269;letter-spacing:0.12em;text-transform:uppercase;font-weight:500">Date</span>', unsafe_allow_html=True)
        hdr[1].markdown('<span style="font-size:0.72rem;color:#7a7269;letter-spacing:0.12em;text-transform:uppercase;font-weight:500">Status</span>', unsafe_allow_html=True)

        st.markdown('<div style="border-top:1px solid #e2dbd0;margin-bottom:0.4rem"></div>', unsafe_allow_html=True)

        for r in records:
            c1, c2 = st.columns([2, 2])
            c1.markdown(
                f'<span style="font-size:0.92rem;color:#2d2a26;font-family:DM Sans,sans-serif">{r["date"]}</span>',
                unsafe_allow_html=True,
            )
            badge_cls = "att-badge-present" if r["status"] == "Present" else "att-badge-absent"
            c2.markdown(f'<span class="{badge_cls}">{r["status"]}</span>', unsafe_allow_html=True)

        return  # end parent view

    # ── ADMIN VIEW  (editable) ────────────────────────────────────
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
        st.info("No students found for the selected filter.")
        return

    existing = {
        r["student_id"]: r["status"]
        for r in db_all("SELECT student_id, status FROM attendance WHERE date=?", (chosen_date,))
    }

    st.markdown("<br>", unsafe_allow_html=True)
    hdr = st.columns([4, 3, 2])
    hdr[0].markdown('<span style="font-size:0.72rem;color:#7a7269;letter-spacing:0.12em;text-transform:uppercase;font-weight:500">Student</span>', unsafe_allow_html=True)
    hdr[1].markdown('<span style="font-size:0.72rem;color:#7a7269;letter-spacing:0.12em;text-transform:uppercase;font-weight:500">Status</span>', unsafe_allow_html=True)
    hdr[2].markdown('<span style="font-size:0.72rem;color:#7a7269;letter-spacing:0.12em;text-transform:uppercase;font-weight:500">Save</span>', unsafe_allow_html=True)
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
        st.success("✅  All attendance records saved.")


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
        st.info("No students found.")
        return

    smap = {s["name"]: s["id"] for s in students}

    if user["role"] == "admin":
        with st.expander("➕  Record Fee Payment"):
            c1, c2, c3, c4 = st.columns(4)
            sel_student = c1.selectbox("Student", list(smap), key="fee_stu")
            month       = c2.selectbox("Month",   MONTHS,     key="fee_mon")
            amount      = c3.number_input("Amount (₹)", min_value=0.0, step=100.0, key="fee_amt")
            status      = c4.selectbox("Status", ["due", "paid"], key="fee_sta")
            if st.button("Save Fee Record", type="primary"):
                ok = db_run(
                    """INSERT INTO fees(student_id,month,amount,status) VALUES(?,?,?,?)
                       ON CONFLICT(student_id,month) DO UPDATE SET amount=excluded.amount, status=excluded.status""",
                    (smap[sel_student], month, amount, status),
                )
                if ok:
                    st.success("Fee record saved ✅")
                    st.rerun()

    student_ids  = list(smap.values())
    placeholders = ",".join("?" * len(student_ids))
    rows = db_all(
        f"""SELECT f.id, s.name AS Student, f.month AS Month,
                   f.amount AS Amount, f.status AS Status
            FROM fees f JOIN students s ON f.student_id=s.id
            WHERE f.student_id IN ({placeholders})
            ORDER BY s.name, f.month""",
        tuple(student_ids),
    )

    if rows:
        df = pd.DataFrame(rows)

        def color_status(val):
            if val == "paid":
                return "background-color:#edf4ef; color:#3d5c47; font-weight:500"
            return "background-color:#fdf0ed; color:#c0614a; font-weight:500"

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
        role     = c1.selectbox("Role", ["parent", "admin"], key="nu_role")
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
                    st.success(f"User '{username}' created ✅")
                    st.rerun()

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
    st.session_state.setdefault("page", "Students")

    st.markdown(
        '<h1 style="text-align:center">✦ Natyashree School of Dance ✦</h1>',
        unsafe_allow_html=True,
    )

    if not st.session_state.user:
        login_page()
        return

    top_menu(st.session_state.user["role"])

    page = st.session_state.page
    if   page == "Students":   students_page()
    elif page == "Classes":    classes_page()
    elif page == "Attendance": attendance_page()
    elif page == "Fees":       fees_page()
    elif page == "Users":      users_page()
    elif page == "Logout":
        st.session_state.user = None
        st.session_state.page = "Students"
        st.rerun()


if __name__ == "__main__":
    main()
