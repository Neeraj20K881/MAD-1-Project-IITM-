"""
models.py
Simple database helper and schema creation for the Placement Portal.
All DB interactions are done here using sqlite3 to keep things easy to follow.
"""
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'placement.db')


def get_db_connection():
    # Returns a sqlite3 connection object configured to return dict-like rows
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def drop_tables():
    conn = sqlite3.connect("placement.db")
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cur.fetchall()

    for table in tables:
        cur.execute(f"DROP TABLE {table[0]}")

    conn.commit()
    conn.close()

def init_db():
    """Create database and tables if they don't exist.

    This function is safe to call multiple times; it will only create tables
    if they don't already exist. It also creates a default admin user.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    #drop_tables()

    # users table: stores login credentials for admin, students and companies

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'student', 'company'))
        )
    ''')

    # students table: profile details for students
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            full_name TEXT,
            department TEXT,
            cgpa REAL,
            phone TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # companies table: profile and approval status
    cur.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            company_name TEXT,
            hr_contact TEXT,
            website TEXT,
            approved INTEGER DEFAULT 0,
            blacklisted INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # drives table: placement drives created by companies
    cur.execute('''
        CREATE TABLE IF NOT EXISTS drives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            job_title TEXT,
            job_desc TEXT,
            eligibility TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','Approved','Closed')),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        )
    ''')

    # applications table: students apply to drives
    cur.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            drive_id INTEGER NOT NULL,
            applied_on TEXT,
            status TEXT DEFAULT 'Applied' CHECK(status IN ('Applied','Shortlisted','Selected','Rejected')),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (drive_id) REFERENCES drives(id) ON DELETE CASCADE,
            UNIQUE(student_id, drive_id) -- prevent duplicate applications
        )
    ''')

    conn.commit()

    # create default admin user if not exists
    cur.execute("SELECT * FROM users WHERE username = ?", ('admin',))
    if cur.fetchone() is None:
        pw = generate_password_hash('adminpass')
        cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', pw, 'admin'))
        conn.commit()

    conn.close()


def create_user(username, password, role):
    # helper to create a user account and return the new user id
    conn = get_db_connection()
    cur = conn.cursor()
    pw_hash = generate_password_hash(password)
    try:
        cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, pw_hash, role))
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        user_id = None
    conn.close()
    return user_id


def verify_user(username, password):
    # Returns user row if credentials OK, else None
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None


def get_user_by_id(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    u = cur.fetchone()
    conn.close()
    return u


def add_student_profile(user_id, full_name='', department='', cgpa=None, phone=''):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO students (user_id, full_name, department, cgpa, phone) VALUES (?, ?, ?, ?, ?)",
                (user_id, full_name, department, cgpa, phone))
    conn.commit()
    conn.close()


def add_company_profile(user_id, company_name='', hr_contact='', website=''):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO companies (user_id, company_name, hr_contact, website) VALUES (?, ?, ?, ?)",
                (user_id, company_name, hr_contact, website))
    conn.commit()
    conn.close()


def get_companies(only_approved=False):
    conn = get_db_connection()
    cur = conn.cursor()
    if only_approved:
        cur.execute("SELECT * FROM companies WHERE approved = 1 AND blacklisted = 0")
    else:
        cur.execute("SELECT * FROM companies")
    rows = cur.fetchall()
    conn.close()
    return rows


def set_company_approval(company_id, approved):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE companies SET approved = ? WHERE id = ?", (1 if approved else 0, company_id))
    conn.commit()
    conn.close()


def set_company_blacklist(company_id, blacklisted):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE companies SET blacklisted = ? WHERE id = ?", (1 if blacklisted else 0, company_id))
    conn.commit()
    conn.close()


def create_drive(company_id, job_title, job_desc, eligibility, deadline):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO drives (company_id, job_title, job_desc, eligibility, deadline, status) VALUES (?, ?, ?, ?, ?, 'Pending')",
                (company_id, job_title, job_desc, eligibility, deadline))
    conn.commit()
    drive_id = cur.lastrowid
    conn.close()
    return drive_id


def get_drives(only_approved=False):
    # Join drives with company info
    conn = get_db_connection()
    cur = conn.cursor()
    if only_approved:
        cur.execute('''SELECT d.*, c.company_name FROM drives d JOIN companies c ON d.company_id = c.id
                       WHERE d.status = 'Approved' AND c.approved = 1 AND c.blacklisted = 0''')
    else:
        cur.execute('''SELECT d.*, c.company_name FROM drives d JOIN companies c ON d.company_id = c.id''')
    rows = cur.fetchall()
    
    conn.close()
    return rows


def set_drive_status(drive_id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE drives SET status = ? WHERE id = ?", (status, drive_id))
    conn.commit()
    conn.close()


def apply_for_drive(student_id, drive_id, applied_on):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO applications (student_id, drive_id, applied_on, status) VALUES (?, ?, ?, 'Applied')",
                    (student_id, drive_id, applied_on))
        conn.commit()
        ok = True
    except sqlite3.IntegrityError:
        ok = False
    conn.close()
    return ok


def get_applications_for_drive(drive_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # include student profile fields so the UI can show department, cgpa and phone
    cur.execute('''SELECT a.*, s.full_name, s.department, s.cgpa, s.phone, u.username as student_username FROM applications a
                   JOIN students s ON a.student_id = s.id
                   JOIN users u ON s.user_id = u.id
                   WHERE a.drive_id = ?''', (drive_id,))
    rows = cur.fetchall()
    for i in range(len(list(rows))):
        print(list(rows[i]))
    
    conn.close()
    return rows


def get_application_by_student_and_drive(student_id, drive_id):
    """Return the application row for a given student and drive or None."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT * FROM applications WHERE student_id = ? AND drive_id = ?''', (student_id, drive_id))
    row = cur.fetchone()
    conn.close()
    return row


def set_application_status(application_id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET status = ? WHERE id = ?", (status, application_id))
    conn.commit()
    conn.close()


def get_student_by_userid(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_company_by_userid(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM companies WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_drive(drive_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT d.*, c.company_name FROM drives d JOIN companies c ON d.company_id = c.id WHERE d.id = ?''', (drive_id,))
    row = cur.fetchone()
    conn.close()
    return row


def count_students():
    """Return total number of student profiles in the system."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM students")
    r = cur.fetchone()
    conn.close()
    return r['cnt'] if r else 0


def count_companies():
    """Return total number of companies in the system."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM companies")
    r = cur.fetchone()
    conn.close()
    return r['cnt'] if r else 0


def search_companies(query):
    """Search companies by name or id (partial match for name).

    Returns list of company rows.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    q_like = f"%{query}%"
    # try to match by id when query is integer
    try:
        q_id = int(query)
    except Exception:
        q_id = None
    if q_id is not None:
        cur.execute("SELECT * FROM companies WHERE company_name LIKE ? OR id = ?", (q_like, q_id))
    else:
        cur.execute("SELECT * FROM companies WHERE company_name LIKE ?", (q_like,))
    rows = cur.fetchall()
    conn.close()
    return rows


def search_students(query):
    """Search students by full name, department, student id or username.

    Returns list of rows with student fields plus username from users table.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    q_like = f"%{query}%"
    # attempt numeric id match
    try:
        q_id = int(query)
    except Exception:
        q_id = None

    if q_id is not None:
        cur.execute('''
            SELECT s.*, u.username FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE s.full_name LIKE ? OR s.department LIKE ? OR s.id = ? OR s.user_id = ? OR u.username LIKE ?
        ''', (q_like, q_like, q_id, q_id, q_like))
    else:
        cur.execute('''
            SELECT s.*, u.username FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE s.full_name LIKE ? OR s.department LIKE ? OR u.username LIKE ?
        ''', (q_like, q_like, q_like))

    rows = cur.fetchall()
    conn.close()
    return rows
