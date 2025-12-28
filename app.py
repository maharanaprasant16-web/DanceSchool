# dance_school_streamlit_app.py
"""
Dance School Management (Streamlit + SQLite + Plotly)

- Admin + Parent logins (hashed passwords)
- Optional DB reset via CLI flag (--reset)
- Admin: Add/Edit/Delete Students, Add/Delete Classes, Attendance (enhanced), Monthly Fees, Create Parent users
- Parent: Auto-linked view of their child's profile, attendance chart, fees
"""

import streamlit as st
import sqlite3
import sys
import hashlib
from datetime import date, datetime
import pandas as pd
import plotly.express as px

DB_PATH = "dance_school.db"
RESET_ON_START = "--reset" in sys.argv

# -------------------------
# DB helpers & initialization
# -------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def execute_sql(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    last = cur.lastrowid
    conn.close()
    return last

def fetchone_dict(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def fetchall_dict(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def verify_password(pw: str, pw_hash: str) -> bool:
    return hash_password(pw) == pw_hash

def init_db(reset: bool = False):
    conn = get_conn()
    cur = conn.cursor()
    if reset:
        cur.execute("DROP TABLE IF EXISTS users")
        cur.execute("DROP TABLE IF EXISTS classes")
        cur.execute("DROP TABLE IF EXISTS students")
        cur.execute("DROP TABLE IF EXISTS attendance")
        cur.execute("DROP TABLE IF EXISTS fees")
        conn.commit()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        student_id INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_type TEXT,
        day_of_week TEXT,
        time TEXT,
        instructor TEXT,
        notes TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        class_id INTEGER,
        contact TEXT,
        guardian_name TEXT,
        admission_date TEXT,
        notes TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER,
        student_id INTEGER,
        date TEXT,
        status TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        amount REAL,
        month TEXT,
        status TEXT,
        paid_date TEXT
    )
    """)
    # ensure admin user exists
    cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role='Admin'")
    cnt = cur.fetchone()["cnt"]
    if cnt == 0:
        cur.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    ("Admin", hash_password("Admin123"), "Admin"))
    conn.commit()
    conn.close()

# -------------------------
# Attendance helper
# -------------------------
def upsert_attendance(class_id: int, student_id: int, dt: str, status: str):
    existing = fetchone_dict("SELECT id FROM attendance WHERE class_id=? AND student_id=? AND date=?",
                             (class_id, student_id, dt))
    if existing:
        execute_sql("UPDATE attendance SET status=? WHERE id=?", (status, existing["id"]))
    else:
        execute_sql("INSERT INTO attendance (class_id, student_id, date, status) VALUES (?, ?, ?, ?)",
                    (class_id, student_id, dt, status))

# -------------------------
# Auth
# -------------------------
def authenticate(username: str, password: str):
    row = fetchone_dict("SELECT * FROM users WHERE username=?", (username,))
    if not row:
        return None
    if not row.get("password_hash"):
        return None
    if verify_password(password, row["password_hash"]):
        return {"id": row["id"], "username": row["username"], "role": row["role"], "student_id": row["student_id"]}
    return None

def create_parent_user(username: str, password: str, student_id=None):
    try:
        execute_sql("INSERT INTO users (username, password_hash, role, student_id) VALUES (?, ?, ?, ?)",
                    (username, hash_password(password), "parent", student_id))
        return True, "Created"
    except sqlite3.IntegrityError:
        return False, "Username exists"

# -------------------------
# Admin pages
# -------------------------
def admin_students_page():
    st.header("Students — Add / Edit / Delete")

    # classes for dropdown
    classes = fetchall_dict("SELECT id, class_type, day_of_week, time FROM classes ORDER BY id")
    class_map = {"Unassigned": None}
    for c in classes:
        class_map[f"{c['class_type']} - {c['day_of_week']} {c['time']} (ID:{c['id']})"] = c["id"]

    with st.form("add_student_form", clear_on_submit=True):
        st.subheader("Add Student")
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=3, max_value=100, value=8)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        class_label = st.selectbox("Class (assign)", list(class_map.keys()))
        class_id = class_map[class_label]
        contact = st.text_input("Contact")
        guardian = st.text_input("Guardian Name")
        notes = st.text_area("Notes")
        add_submitted = st.form_submit_button("Add Student")
    if add_submitted:
        if not name.strip():
            st.error("Student name required")
        else:
            execute_sql("""INSERT INTO students (name, age, gender, class_id, contact, guardian_name, admission_date, notes)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (name.strip(), int(age), gender, class_id, contact.strip() or None, guardian.strip() or None, date.today().isoformat(), notes.strip() or None))
            st.success(f"Added student: {name.strip()}")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Students List")
    students = fetchall_dict("""
        SELECT s.id, s.name, s.age, s.gender, s.contact, s.guardian_name, s.class_id,
               c.class_type, c.day_of_week, c.time
        FROM students s LEFT JOIN classes c ON s.class_id=c.id
        ORDER BY s.id DESC
    """)
    if not students:
        st.info("No students yet.")
    else:
        df = pd.DataFrame(students)
        df['class'] = df.apply(lambda r: f"{r.get('class_type') or ''} {r.get('day_of_week') or ''} {r.get('time') or ''}".strip()
                               if r.get('class_type') else "Unassigned", axis=1)
        st.dataframe(df[['id','name','age','gender','guardian_name','contact','class']])

        st.markdown("### Manage individual students")
        for s in students:
            c1, c2 = st.columns([6,1])
            c1.write(f"**{s['name']}** — Parent: {s.get('guardian_name') or '-'} — Contact: {s.get('contact') or '-'} — Class ID: {s.get('class_id') or 'Unassigned'}")
            if c2.button("Edit", key=f"edit_{s['id']}"):
                st.session_state["editing_student_id"] = s['id']
            if c2.button("Delete", key=f"del_{s['id']}"):
                execute_sql("DELETE FROM students WHERE id=?", (s['id'],))
                st.success("Deleted.")
                st.experimental_rerun()

    # Edit form if requested
    if st.session_state.get("editing_student_id"):
        sid = st.session_state["editing_student_id"]
        rec = fetchone_dict("SELECT * FROM students WHERE id=?", (sid,))
        if rec:
            st.markdown("---")
            st.subheader(f"Edit Student: {rec['name']}")
            with st.form("edit_student_form"):
                new_name = st.text_input("Name", value=rec['name'])
                new_age = st.number_input("Age", min_value=3, max_value=100, value=rec.get('age') or 8)
                gender_opts = ["Male","Female","Other"]
                try:
                    gender_index = gender_opts.index(rec.get('gender')) if rec.get('gender') in gender_opts else 0
                except Exception:
                    gender_index = 0
                new_gender = st.selectbox("Gender", gender_opts, index=gender_index)
                # class dropdown
                class_labels = list(class_map.keys())
                try:
                    default_index = list(class_map.values()).index(rec.get('class_id'))
                except ValueError:
                    default_index = 0
                new_class_label = st.selectbox("Class", class_labels, index=default_index)
                new_class_id = class_map[new_class_label]
                new_contact = st.text_input("Contact", value=rec.get('contact') or "")
                new_guardian = st.text_input("Guardian Name", value=rec.get('guardian_name') or "")
                new_notes = st.text_area("Notes", value=rec.get('notes') or "")
                save_submitted = st.form_submit_button("Save Changes")
            if save_submitted:
                execute_sql("""UPDATE students SET name=?, age=?, gender=?, class_id=?, contact=?, guardian_name=?, notes=?
                               WHERE id=?""",
                            (new_name.strip(), int(new_age), new_gender, new_class_id, new_contact.strip() or None, new_guardian.strip() or None, new_notes.strip() or None, sid))
                st.success("Student updated")
                del st.session_state["editing_student_id"]
                st.experimental_rerun()

def admin_classes_page():
    st.header("Classes — Add / Delete")
    with st.form("add_class_form", clear_on_submit=True):
        class_type = st.selectbox("Class Type", ["Bharatanatyam","Modern","Singing"])
        day = st.selectbox("Day of Week", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
        time_str = st.text_input("Time (e.g. 5:00 PM)")
        instructor = st.text_input("Instructor")
        notes = st.text_area("Notes")
        add_class_submitted = st.form_submit_button("Add Class")
    if add_class_submitted:
        if not time_str.strip():
            st.error("Enter class time")
        else:
            execute_sql("INSERT INTO classes (class_type, day_of_week, time, instructor, notes) VALUES (?,?,?,?,?)",
                        (class_type, day, time_str.strip(), instructor.strip() or None, notes.strip() or None))
            st.success("Class added")
            st.experimental_rerun()

    st.markdown("---")
    classes = fetchall_dict("SELECT * FROM classes ORDER BY id DESC")
    if not classes:
        st.info("No classes yet.")
    else:
        df = pd.DataFrame(classes)
        df['label'] = df.apply(lambda r: f"{r.get('class_type','')} - {r.get('day_of_week','')} {r.get('time','')}".strip(), axis=1)
        st.dataframe(df[['id','label','instructor','notes']])
        for c in classes:
            c1, c2 = st.columns([6,1])
            c1.write(f"**{c['class_type']}** — {c['day_of_week']} {c['time']} (ID:{c['id']}) — Instructor: {c.get('instructor') or '-'}")
            if c2.button("Delete", key=f"delclass_{c['id']}"):
                execute_sql("UPDATE students SET class_id=NULL WHERE class_id=?", (c['id'],))
                execute_sql("DELETE FROM classes WHERE id=?", (c['id'],))
                st.success("Class deleted (students unassigned)")
                st.experimental_rerun()
def admin_attendance_page():
    st.header("Attendance (Enhanced)")

    # Fetch classes
    classes = fetchall_dict("SELECT id, class_type, day_of_week, time FROM classes ORDER BY id")
    if not classes:
        st.info("No classes available. Add classes first.")
        return

    class_options = {c['id']: f"{c['class_type']} - {c['day_of_week']} {c['time']}" for c in classes}
    class_id_list = list(class_options.keys())
    class_labels_list = list(class_options.values())

    # Fetch students
    students = fetchall_dict("""
        SELECT s.id, s.name, s.class_id, c.class_type, c.day_of_week, c.time
        FROM students s LEFT JOIN classes c ON s.class_id=c.id
        ORDER BY s.name
    """)
    if not students:
        st.info("No students found. Add students first.")
        return

    # Default class
    chosen_default_label = st.selectbox("Default Class (for quick set)", class_labels_list, index=0)
    chosen_default_id = [cid for cid, lbl in class_options.items() if lbl == chosen_default_label][0]

    st.markdown("### Mark attendance for each student")

    with st.form("attendance_bulk_form"):
        status_map = {}
        class_map = {}

        for s in students:
            cols = st.columns([3, 3, 4])
            cols[0].write(s['name'])

            # Attendance radio
            status = cols[1].radio(
                "Status",
                ["Present", "Absent"],
                key=f"att_status_{s['id']}",
                horizontal=True
            )
            status_map[s['id']] = status

            # Class dropdown
            default_for_student = s.get('class_id') or chosen_default_id
            try:
                default_index = class_id_list.index(default_for_student)
            except ValueError:
                default_index = 0
            selected_label = cols[2].selectbox(
                "Class (day/time)",
                class_labels_list,
                index=default_index,
                key=f"att_class_{s['id']}"
            )
            class_map[s['id']] = selected_label

        attendance_submitted = st.form_submit_button("Save All Attendance")

    if attendance_submitted:
        today = date.today().isoformat()
        saved = 0
        for s in students:
            status = status_map[s['id']]
            selected_label = class_map[s['id']]
            sel_ids = [cid for cid, lbl in class_options.items() if lbl == selected_label]
            sel_cid = sel_ids[0] if sel_ids else chosen_default_id
            upsert_attendance(sel_cid, s['id'], today, status)
            saved += 1
        st.success(f"Saved attendance for {saved} students")
        st.experimental_rerun()

    st.markdown("---")
    st.subheader("Attendance Records (latest first)")
    records = fetchall_dict("""
        SELECT a.id, s.name as student_name, c.class_type, c.day_of_week, c.time, a.date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN classes c ON a.class_id = c.id
        ORDER BY a.date DESC, a.id DESC
    """)
    if records:
        df = pd.DataFrame(records)
        st.dataframe(df)
    else:
        st.info("No attendance records yet.")

def admin_fees_page():
    st.header("Fees — Record & View")
    students = fetchall_dict("SELECT id, name FROM students ORDER BY name")
    if not students:
        st.info("Add students first.")
        return
    student_map = { f"{s['name']} (ID:{s['id']})": s['id'] for s in students }

    with st.form("fee_form", clear_on_submit=True):
        sel = st.selectbox("Select Student", list(student_map.keys()))
        sid = student_map[sel]
        month = st.selectbox("Month", ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"])
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        status = st.selectbox("Status", ["due","paid","partial"])
        fee_submitted = st.form_submit_button("Record Fee")
    if fee_submitted:
        execute_sql("INSERT INTO fees (student_id, amount, month, status, paid_date) VALUES (?,?,?,?,?)",
                    (sid, float(amount), month, status, date.today().isoformat()))
        st.success("Fee recorded")
        st.experimental_rerun()

    st.markdown("---")
    st.subheader("Fee Records")
    fees = fetchall_dict("""SELECT f.id, s.name as student_name, f.month, f.amount, f.status, f.paid_date
                            FROM fees f JOIN students s ON f.student_id = s.id
                            ORDER BY f.id DESC""")
    if fees:
        st.dataframe(pd.DataFrame(fees))
    else:
        st.info("No fee records yet.")

def admin_users_page():
    st.header("Users — Create Parent Account (link to student)")
    students = fetchall_dict("SELECT id, name FROM students ORDER BY name")
    student_map = {"Not linked": None}
    for s in students:
        student_map[f"{s['name']} (ID:{s['id']})"] = s['id']

    with st.form("create_parent_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        student_label = st.selectbox("Link to Student", list(student_map.keys()))
        student_id = student_map[student_label]
        parent_submitted = st.form_submit_button("Create Parent Account")
    if parent_submitted:
        if not username or not password:
            st.error("Provide username & password")
        else:
            ok, msg = create_parent_user(username, password, student_id)
            if ok:
                st.success("Parent account created")
            else:
                st.error(msg)

# -------------------------
# Parent pages
# -------------------------
def parent_dashboard(user):
    st.header("Parent Dashboard")
    sid = user.get("student_id")
    if not sid:
        st.info("Your account is not linked to a student. Contact admin.")
        return
    s = fetchone_dict("SELECT s.*, c.class_type, c.day_of_week, c.time FROM students s LEFT JOIN classes c ON s.class_id=c.id WHERE s.id=?", (sid,))
    if not s:
        st.error("Linked student not found.")
        return

    st.subheader(f"Student: {s['name']}")
    st.write(f"Age: {s.get('age') or '-'} | Parent: {s.get('guardian_name') or '-'} | Contact: {s.get('contact') or '-'}")
    st.write(f"Class: { (s.get('class_type') or '') + ' ' + (s.get('day_of_week') or '') + ' ' + (s.get('time') or '') }")

    st.markdown("---")
    st.subheader("Attendance")
    rows = fetchall_dict("SELECT date, status FROM attendance WHERE student_id=? ORDER BY date DESC", (sid,))
    if rows:
        df = pd.DataFrame(rows)
        df['present'] = df['status'].apply(lambda x: 1 if x=="Present" else 0)
        st.dataframe(df)
        fig = px.bar(df, x='date', y='present', labels={'present':'Present(1)/Absent(0)'}, title="Attendance")
        st.plotly_chart(fig)
        st.write(f"Recorded days: {len(df)} — Present%: {df['present'].mean()*100:.1f}%")
    else:
        st.info("No attendance records yet.")

    st.markdown("---")
    st.subheader("Fees")
    fees = fetchall_dict("SELECT month, amount, status, paid_date FROM fees WHERE student_id=? ORDER BY id DESC", (sid,))
    if fees:
        st.dataframe(pd.DataFrame(fees))
    else:
        st.info("No fee records yet.")

# -------------------------
# Main app
# -------------------------
def main():
    st.set_page_config(page_title="Natyashree School of Dance", layout="wide")
    
    st.title("💃Natyashree School of Dance💃")
   

    # initialize DB (reset optional)
    init_db(reset=RESET_ON_START)

    # ensure session_state key exists
    if "user" not in st.session_state:
        st.session_state["user"] = None

    # login
    if st.session_state["user"] is None:
        st.sidebar.header("Login")
        uname = st.sidebar.text_input("Username")
        pwd = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            user = authenticate(uname, pwd)
            if user:
                st.session_state["user"] = user
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid credentials")
        st.sidebar.markdown("---")
        #st.sidebar.info("Default admin: username=`admin` password=`admin123` (use --reset to recreate DB if needed)")
        return

    # logged in
    user = st.session_state["user"]
    st.sidebar.success(f"Logged in as: {user['username']} ({user['role']})")
    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.experimental_rerun()

    # admin reset DB button (destructive)
    if user.get("role") == "admin":
        if st.sidebar.button("Reset DB (wipe ALL data)"):
            init_db(reset=True)
            st.sidebar.success("DB reset. Please login again.")
            st.session_state["user"] = None
            st.experimental_rerun()

    # routing
    if user.get("role") == "admin":
        page = st.sidebar.selectbox("Admin Menu", ["Students","Classes","Attendance","Fees","Users"])
        if page == "Students":
            admin_students_page()
        elif page == "Classes":
            admin_classes_page()
        elif page == "Attendance":
            admin_attendance_page()
        elif page == "Fees":
            admin_fees_page()
        elif page == "Users":
            admin_users_page()
    elif user.get("role") == "parent":
        parent_dashboard(user)
    else:
        st.error("Unknown role")
      

if __name__ == "__main__":
    main()
