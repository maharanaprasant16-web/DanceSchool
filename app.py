import streamlit as st
import sqlite3
import hashlib
from datetime import date
import pandas as pd
from contextlib import contextmanager

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
st.set_page_config(page_title="Natyashree School of Dance", layout="wide")

DB = "dance_school.db"
DAYS   = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

ADMIN_PAGES  = ["Students", "Classes", "Attendance", "Fees", "Users", "Logout"]
PARENT_PAGES = ["Attendance", "Fees", "Logout"]


# ─────────────────────────────────────────
# DB HELPERS  (no builtin shadowing)
# ─────────────────────────────────────────
@contextmanager
def get_conn():
    """Yield a connection and always close it."""
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
    """INSERT / UPDATE / DELETE. Returns True on success."""
    try:
        with get_conn() as c:
            c.execute(sql, params)
        return True
    except sqlite3.Error as e:
        st.error(f"DB error: {e}")
        return False


def db_all(sql: str, params: tuple = ()) -> list[dict]:
    """Return all rows as list of dicts."""
    try:
        with get_conn() as c:
            rows = c.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        st.error(f"DB error: {e}")
        return []


def db_one(sql: str, params: tuple = ()) -> dict | None:
    rows = db_all(sql, params)
    return rows[0] if rows else None


# ─────────────────────────────────────────
# DB INIT  (idempotent)
# ─────────────────────────────────────────
def init_db():
    ddl_statements = [
        """CREATE TABLE IF NOT EXISTS users(
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role          TEXT NOT NULL CHECK(role IN ('admin','parent')),
            student_id    INTEGER REFERENCES students(id)
        )""",
        """CREATE TABLE IF NOT EXISTS classes(
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            day        TEXT NOT NULL,
            time       TEXT NOT NULL,
            instructor TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS students(
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            age      INTEGER NOT NULL,
            gender   TEXT NOT NULL,
            class_id INTEGER REFERENCES classes(id),
            guardian TEXT,
            contact  TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS attendance(
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            class_id   INTEGER REFERENCES classes(id),
            date       TEXT NOT NULL,
            status     TEXT NOT NULL,
            UNIQUE(student_id, date)          -- prevent duplicates
        )""",
        """CREATE TABLE IF NOT EXISTS fees(
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            month      TEXT NOT NULL,
            amount     REAL NOT NULL,
            status     TEXT NOT NULL CHECK(status IN ('due','paid')),
            UNIQUE(student_id, month)         -- one record per student per month
        )""",
    ]
    with get_conn() as c:
        for stmt in ddl_statements:
            c.execute(stmt)

    # Default admin (only if none exists)
    if not db_one("SELECT 1 FROM users WHERE role='admin'"):
        db_run(
            "INSERT OR IGNORE INTO users(username, password_hash, role) VALUES(?,?,?)",
            ("admin", hash_pw("admin123"), "admin"),
        )


# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────
def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username: str, password: str) -> dict | None:
    user = db_one("SELECT * FROM users WHERE username=?", (username,))
    if user and user["password_hash"] == hash_pw(password):
        return user
    return None


# ─────────────────────────────────────────
# LAYOUT HELPERS
# ─────────────────────────────────────────
def top_menu(role: str):
    pages = ADMIN_PAGES if role == "admin" else PARENT_PAGES
    cols  = st.columns(len(pages))
    for col, page in zip(cols, pages):
        if col.button(page, use_container_width=True):
            st.session_state.page = page
            st.rerun()


def require_admin():
    if st.session_state.user.get("role") != "admin":
        st.warning("Access denied.")
        st.stop()


# ─────────────────────────────────────────
# PAGE: STUDENTS
# ─────────────────────────────────────────
def students_page():
    require_admin()
    st.header("👩‍🎓 Students")

    classes = db_all("SELECT id, name FROM classes ORDER BY name")
    class_options = {c["name"]: c["id"] for c in classes}
    class_options_with_none = {"— None —": None, **class_options}

    # ── Add student ──────────────────────────────────────────────────
    with st.expander("➕ Add Student"):
        col1, col2 = st.columns(2)
        with col1:
            name    = st.text_input("Full Name", key="new_s_name")
            age     = st.number_input("Age", min_value=3, max_value=100, key="new_s_age")
            gender  = st.selectbox("Gender", ["Female", "Male", "Other"], key="new_s_gender")
        with col2:
            cls     = st.selectbox("Class", list(class_options_with_none), key="new_s_class")
            guardian = st.text_input("Guardian Name", key="new_s_guardian")
            contact  = st.text_input("Contact Number", key="new_s_contact")

        if st.button("➕ Add Student", type="primary"):
            if not name.strip():
                st.warning("Name is required.")
            else:
                ok = db_run(
                    "INSERT INTO students(name,age,gender,class_id,guardian,contact) VALUES(?,?,?,?,?,?)",
                    (name.strip(), age, gender, class_options_with_none[cls], guardian, contact),
                )
                if ok:
                    st.success(f"✅ '{name}' added.")
                    st.rerun()

    # ── List / edit / delete ─────────────────────────────────────────
    students = db_all("SELECT s.*, c.name AS class_name FROM students s LEFT JOIN classes c ON s.class_id=c.id ORDER BY s.name")
    if not students:
        st.info("No students yet.")
        return

    for s in students:
        label = f"{s['name']}  •  {s.get('class_name') or 'No class'}  •  Age {s['age']}"
        with st.expander(label):
            c1, c2 = st.columns(2)
            with c1:
                new_name = st.text_input("Name",    s["name"],    key=f"sn{s['id']}")
                new_age  = st.number_input("Age", 3, 100, s["age"], key=f"sa{s['id']}")
                new_gen  = st.selectbox("Gender", ["Female","Male","Other"],
                                        index=["Female","Male","Other"].index(s["gender"]) if s["gender"] in ["Female","Male","Other"] else 0,
                                        key=f"sg{s['id']}")
            with c2:
                new_cls_key  = st.selectbox("Class", list(class_options_with_none),
                                            index=list(class_options_with_none.values()).index(s["class_id"])
                                            if s["class_id"] in class_options_with_none.values() else 0,
                                            key=f"sc{s['id']}")
                new_guardian = st.text_input("Guardian", s.get("guardian") or "", key=f"sgu{s['id']}")
                new_contact  = st.text_input("Contact",  s.get("contact")  or "", key=f"sco{s['id']}")

            b1, b2 = st.columns(2)
            if b1.button("💾 Update", key=f"su{s['id']}"):
                db_run(
                    "UPDATE students SET name=?,age=?,gender=?,class_id=?,guardian=?,contact=? WHERE id=?",
                    (new_name, new_age, new_gen, class_options_with_none[new_cls_key], new_guardian, new_contact, s["id"]),
                )
                st.success("Updated ✅")
                st.rerun()
            if b2.button("🗑️ Delete", key=f"sd{s['id']}"):
                db_run("DELETE FROM students WHERE id=?", (s["id"],))
                st.warning(f"'{s['name']}' deleted.")
                st.rerun()


# ─────────────────────────────────────────
# PAGE: CLASSES
# ─────────────────────────────────────────
def classes_page():
    require_admin()
    st.header("🎓 Classes")

    with st.expander("➕ Add Class"):
        c1, c2 = st.columns(2)
        name       = c1.text_input("Class Name",  key="new_c_name")
        instructor = c2.text_input("Instructor",  key="new_c_inst")
        day        = c1.selectbox("Day", DAYS,    key="new_c_day")
        time_val   = c2.text_input("Time (e.g. 5:00 PM)", key="new_c_time")

        if st.button("➕ Add Class", type="primary"):
            if not name.strip():
                st.warning("Class name is required.")
            else:
                ok = db_run(
                    "INSERT INTO classes(name,day,time,instructor) VALUES(?,?,?,?)",
                    (name.strip(), day, time_val, instructor),
                )
                if ok:
                    st.success(f"✅ Class '{name}' added.")
                    st.rerun()

    classes = db_all("SELECT * FROM classes ORDER BY day, time")
    if not classes:
        st.info("No classes yet.")
        return

    for cls in classes:
        with st.expander(f"{cls['name']}  •  {cls['day']}  {cls['time']}  •  {cls['instructor']}"):
            c1, c2 = st.columns(2)
            new_name = c1.text_input("Name",       cls["name"],       key=f"cn{cls['id']}")
            new_inst = c2.text_input("Instructor",  cls["instructor"], key=f"ci{cls['id']}")
            new_day  = c1.selectbox("Day", DAYS, index=DAYS.index(cls["day"]) if cls["day"] in DAYS else 0, key=f"cd{cls['id']}")
            new_time = c2.text_input("Time",       cls["time"],       key=f"ct{cls['id']}")

            b1, b2 = st.columns(2)
            if b1.button("💾 Update", key=f"cu{cls['id']}"):
                db_run(
                    "UPDATE classes SET name=?,day=?,time=?,instructor=? WHERE id=?",
                    (new_name, new_day, new_time, new_inst, cls["id"]),
                )
                st.success("Updated ✅")
                st.rerun()
            if b2.button("🗑️ Delete", key=f"cdel{cls['id']}"):
                db_run("DELETE FROM classes WHERE id=?", (cls["id"],))
                st.warning(f"Class '{cls['name']}' deleted.")
                st.rerun()


# ─────────────────────────────────────────
# PAGE: ATTENDANCE
# ─────────────────────────────────────────
def attendance_page():
    st.header("📋 Attendance")
    today = date.today().isoformat()

    # Admins can pick any date; parents see today only
    if st.session_state.user["role"] == "admin":
        chosen_date = st.date_input("Date", value=date.today()).isoformat()
    else:
        chosen_date = today
        st.info(f"Showing attendance for today: {today}")

    # Filter by class
    classes = db_all("SELECT * FROM classes ORDER BY name")
    class_options = {"All Classes": None, **{c["name"]: c["id"] for c in classes}}
    filter_cls = st.selectbox("Filter by Class", list(class_options))
    selected_class_id = class_options[filter_cls]

    # Fetch students
    if selected_class_id:
        students = db_all("SELECT * FROM students WHERE class_id=? ORDER BY name", (selected_class_id,))
    else:
        students = db_all("SELECT * FROM students WHERE class_id IS NOT NULL ORDER BY name")

    if not students:
        st.info("No students found for the selected filter.")
        return

    # Load existing attendance for chosen date
    existing = {
        r["student_id"]: r["status"]
        for r in db_all("SELECT student_id, status FROM attendance WHERE date=?", (chosen_date,))
    }

    st.markdown("---")
    header = st.columns([4, 3, 2])
    header[0].markdown("**Student**")
    header[1].markdown("**Status**")
    header[2].markdown("**Action**")

    for s in students:
        c1, c2, c3 = st.columns([4, 3, 2])
        c1.write(s["name"])
        current = existing.get(s["id"], "Present")
        status = c2.radio(
            "Status", ["Present", "Absent"],
            index=0 if current == "Present" else 1,
            horizontal=True,
            key=f"att_{s['id']}_{chosen_date}",
            label_visibility="collapsed",
        )
        if c3.button("Save", key=f"asave_{s['id']}_{chosen_date}"):
            # UPSERT – handles duplicate gracefully
            db_run(
                """INSERT INTO attendance(student_id, class_id, date, status) VALUES(?,?,?,?)
                   ON CONFLICT(student_id, date) DO UPDATE SET status=excluded.status""",
                (s["id"], s.get("class_id"), chosen_date, status),
            )
            st.success(f"Saved {s['name']}: {status}")

    # Bulk save all
    if st.button("💾 Save All", type="primary"):
        for s in students:
            widget_key = f"att_{s['id']}_{chosen_date}"
            status = st.session_state.get(widget_key, "Present")
            db_run(
                """INSERT INTO attendance(student_id, class_id, date, status) VALUES(?,?,?,?)
                   ON CONFLICT(student_id, date) DO UPDATE SET status=excluded.status""",
                (s["id"], s.get("class_id"), chosen_date, status),
            )
        st.success("✅ All attendance saved.")


# ─────────────────────────────────────────
# PAGE: FEES
# ─────────────────────────────────────────
def fees_page():
    st.header("💰 Fees")

    # Parents see only their linked student
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
        with st.expander("➕ Record Fee Payment"):
            c1, c2, c3, c4 = st.columns(4)
            selected_student = c1.selectbox("Student", list(smap))
            month  = c2.selectbox("Month", MONTHS)
            amount = c3.number_input("Amount (₹)", min_value=0.0, step=100.0)
            status = c4.selectbox("Status", ["due", "paid"])

            if st.button("💾 Save Fee", type="primary"):
                ok = db_run(
                    """INSERT INTO fees(student_id, month, amount, status) VALUES(?,?,?,?)
                       ON CONFLICT(student_id, month) DO UPDATE SET amount=excluded.amount, status=excluded.status""",
                    (smap[selected_student], month, amount, status),
                )
                if ok:
                    st.success("Fee record saved ✅")
                    st.rerun()

    # ── Summary table ──────────────────────────────────────────────
    student_ids = list(smap.values())
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
        # Color-code status
        def highlight_status(val):
            return "background-color: #d4edda" if val == "paid" else "background-color: #f8d7da"

        st.dataframe(
            df.drop(columns=["id"]).style.applymap(highlight_status, subset=["Status"]),
            use_container_width=True,
        )

        # Quick stats
        total_due  = sum(r["Amount"] for r in rows if r["Status"] == "due")
        total_paid = sum(r["Amount"] for r in rows if r["Status"] == "paid")
        m1, m2 = st.columns(2)
        m1.metric("Total Paid ✅", f"₹{total_paid:,.0f}")
        m2.metric("Total Due ⚠️",  f"₹{total_due:,.0f}")
    else:
        st.info("No fee records found.")


# ─────────────────────────────────────────
# PAGE: USERS  (admin only)
# ─────────────────────────────────────────
def users_page():
    require_admin()
    st.header("👤 Users")

    students = db_all("SELECT id, name FROM students ORDER BY name")
    smap = {"— None —": None, **{s["name"]: s["id"] for s in students}}

    with st.expander("➕ Create User"):
        c1, c2 = st.columns(2)
        username = c1.text_input("Username")
        password = c2.text_input("Password", type="password")
        role     = c1.selectbox("Role", ["parent", "admin"])
        linked   = c2.selectbox("Link to Student", list(smap))

        if st.button("➕ Create User", type="primary"):
            if not username.strip() or not password:
                st.warning("Username and password are required.")
            elif db_one("SELECT 1 FROM users WHERE username=?", (username,)):
                st.error("Username already exists.")
            else:
                ok = db_run(
                    "INSERT INTO users(username, password_hash, role, student_id) VALUES(?,?,?,?)",
                    (username.strip(), hash_pw(password), role, smap[linked]),
                )
                if ok:
                    st.success(f"User '{username}' created ✅")
                    st.rerun()

    st.markdown("---")
    users = db_all("SELECT id, username, role, student_id FROM users ORDER BY role, username")
    if users:
        st.dataframe(pd.DataFrame(users), use_container_width=True)

    # Change password
    with st.expander("🔑 Change Password"):
        unames = [u["username"] for u in users]
        target = st.selectbox("User", unames, key="cpw_user")
        new_pw = st.text_input("New Password", type="password", key="cpw_pw")
        if st.button("Update Password"):
            if not new_pw:
                st.warning("Password cannot be empty.")
            else:
                db_run("UPDATE users SET password_hash=? WHERE username=?", (hash_pw(new_pw), target))
                st.success("Password updated ✅")


# ─────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────
def login_page():
    st.markdown("## 🔐 Login")
    col, _ = st.columns([1, 2])
    with col:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            user = authenticate(username, password)
            if user:
                st.session_state.user = user
                st.session_state.page = "Students" if user["role"] == "admin" else "Attendance"
                st.rerun()
            else:
                st.error("Invalid username or password.")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    init_db()

    # Session defaults
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "Students")

    st.title("💃 Natyashree School of Dance")

    if not st.session_state.user:
        login_page()
        return

    top_menu(st.session_state.user["role"])

    page = st.session_state.page
    if page == "Students":   students_page()
    elif page == "Classes":  classes_page()
    elif page == "Attendance": attendance_page()
    elif page == "Fees":     fees_page()
    elif page == "Users":    users_page()
    elif page == "Logout":
        st.session_state.user = None
        st.session_state.page = "Students"
        st.rerun()


if __name__ == "__main__":
    main()
