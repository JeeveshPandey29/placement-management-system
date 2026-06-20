import os
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)


@contextmanager
def get_db():
    conn = pool.getconn()
    try:
        with conn.cursor() as cursor:
            yield cursor
        conn.commit()
    except Exception as e:
        print("Database transaction error:", e)
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def _col_exists(cur, table, column):
    cur.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
    """, (table, column))
    return cur.fetchone() is not None


def _table_exists(cur, table):
    cur.execute("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
    """, (table,))
    return cur.fetchone() is not None


def init_db():
    with get_db() as cur:

        # ── 1. Drop old incompatible tables from setup.sql ────────────────────
        # Only drop if they have the OLD schema (first_name column = old users table)
        cur.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public' AND table_name='users' AND column_name='first_name'
        """)
        if cur.fetchone():
            print("Dropping old schema tables...")
            cur.execute("DROP TABLE IF EXISTS activity_logs CASCADE;")
            cur.execute("DROP TABLE IF EXISTS interviews CASCADE;")
            cur.execute("DROP TABLE IF EXISTS applications CASCADE;")
            cur.execute("DROP TABLE IF EXISTS assessment_results CASCADE;")
            cur.execute("DROP TABLE IF EXISTS trainers CASCADE;")
            cur.execute("DROP TABLE IF EXISTS students CASCADE;")
            cur.execute("DROP TABLE IF EXISTS users CASCADE;")

        # ── 2. Colleges ───────────────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS colleges (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                location VARCHAR(255) NOT NULL
            );
        ''')

        # ── 3. PMS Users ──────────────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pms_users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'student'
                    CHECK (role IN ('admin', 'trainer', 'student')),
                full_name VARCHAR(255),
                must_change_password BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        ''')
        for col, defn in [
            ("full_name", "VARCHAR(255)"),
            ("must_change_password", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()"),
        ]:
            if not _col_exists(cur, "pms_users", col):
                cur.execute(f"ALTER TABLE pms_users ADD COLUMN {col} {defn};")

        # ── 4. Student Profiles ───────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS student_profiles (
                user_id INTEGER PRIMARY KEY REFERENCES pms_users(id) ON DELETE CASCADE,
                enrollment_number VARCHAR(100),
                roll_number VARCHAR(100),
                college_id INTEGER REFERENCES colleges(id) ON DELETE SET NULL,
                branch VARCHAR(100),
                gpa NUMERIC(4,2) DEFAULT 0.00,
                phone VARCHAR(20),
                dob DATE,
                address TEXT,
                resume_summary TEXT,
                skills TEXT,
                education JSONB DEFAULT '[]'::jsonb,
                projects JSONB DEFAULT '[]'::jsonb,
                certifications JSONB DEFAULT '[]'::jsonb,
                linkedin_url TEXT,
                github_url TEXT,
                portfolio_url TEXT,
                resume_url TEXT,
                status VARCHAR(50) DEFAULT 'unplaced'
                    CHECK (status IN ('unplaced', 'placed'))
            );
        ''')
        for col, defn in [
            ("enrollment_number", "VARCHAR(100)"),
            ("roll_number", "VARCHAR(100)"),
            ("phone", "VARCHAR(20)"),
            ("dob", "DATE"),
            ("address", "TEXT"),
            ("resume_summary", "TEXT"),
            ("skills", "TEXT"),
            ("education", "JSONB DEFAULT '[]'::jsonb"),
            ("projects", "JSONB DEFAULT '[]'::jsonb"),
            ("certifications", "JSONB DEFAULT '[]'::jsonb"),
            ("linkedin_url", "TEXT"),
            ("github_url", "TEXT"),
            ("portfolio_url", "TEXT"),
            ("resume_url", "TEXT"),
        ]:
            if not _col_exists(cur, "student_profiles", col):
                cur.execute(f"ALTER TABLE student_profiles ADD COLUMN {col} {defn};")

        # ── 5. Batches ────────────────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS batches (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                branch VARCHAR(100),
                trainer_id INTEGER REFERENCES pms_users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        ''')

        # ── 6. Batch Students ─────────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS batch_students (
                batch_id INTEGER REFERENCES batches(id) ON DELETE CASCADE,
                student_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                PRIMARY KEY (batch_id, student_id)
            );
        ''')

        # ── 7. Classes ────────────────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                id SERIAL PRIMARY KEY,
                batch_id INTEGER REFERENCES batches(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                class_date DATE NOT NULL,
                start_time TIME,
                end_time TIME,
                location VARCHAR(255),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        ''')

        # ── 8. Notifications ──────────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                target_type VARCHAR(20) NOT NULL DEFAULT 'all'
                    CHECK (target_type IN ('all', 'batch', 'student')),
                target_id INTEGER,
                created_by INTEGER REFERENCES pms_users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        ''')

        # ── 9. Notification Reads ─────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS notification_reads (
                notification_id INTEGER REFERENCES notifications(id) ON DELETE CASCADE,
                student_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                read_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (notification_id, student_id)
            );
        ''')

        # ── 10. Password Reset Tokens ─────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                used BOOLEAN DEFAULT FALSE
            );
        ''')

        # ── 11. Attendance ────────────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                date DATE NOT NULL,
                status VARCHAR(50) NOT NULL CHECK (status IN ('present', 'absent', 'late')),
                session_name VARCHAR(255) NOT NULL
            );
        ''')
        for col, defn in [
            ("batch_id", "INTEGER REFERENCES batches(id) ON DELETE SET NULL"),
            ("class_id", "INTEGER REFERENCES classes(id) ON DELETE SET NULL"),
        ]:
            if not _col_exists(cur, "attendance", col):
                cur.execute(f"ALTER TABLE attendance ADD COLUMN {col} {defn};")

        # ── 12. Assessments ───────────────────────────────────────────────────
        # Handle old schema: total_marks → max_score, assessment_date → date
        cur.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                max_score INTEGER NOT NULL DEFAULT 100,
                date DATE NOT NULL DEFAULT CURRENT_DATE
            );
        ''')
        # migrate old column names if needed
        if _col_exists(cur, "assessments", "total_marks") and not _col_exists(cur, "assessments", "max_score"):
            cur.execute("ALTER TABLE assessments RENAME COLUMN total_marks TO max_score;")
        elif not _col_exists(cur, "assessments", "max_score"):
            cur.execute("ALTER TABLE assessments ADD COLUMN max_score INTEGER NOT NULL DEFAULT 100;")

        if _col_exists(cur, "assessments", "assessment_date") and not _col_exists(cur, "assessments", "date"):
            cur.execute("ALTER TABLE assessments RENAME COLUMN assessment_date TO date;")
        elif not _col_exists(cur, "assessments", "date"):
            cur.execute("ALTER TABLE assessments ADD COLUMN date DATE NOT NULL DEFAULT CURRENT_DATE;")

        if not _col_exists(cur, "assessments", "batch_id"):
            cur.execute("ALTER TABLE assessments ADD COLUMN batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL;")

        # ── 13. Assessment Scores ─────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS assessment_scores (
                id SERIAL PRIMARY KEY,
                assessment_id INTEGER REFERENCES assessments(id) ON DELETE CASCADE,
                student_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                score NUMERIC(5,2) NOT NULL,
                feedback TEXT,
                UNIQUE(assessment_id, student_id)
            );
        ''')

        # ── 14. Placement Drives ──────────────────────────────────────────────
        # Handle old schema: drive_date → date, missing package_lpa / eligibility_cgpa
        cur.execute('''
            CREATE TABLE IF NOT EXISTS placement_drives (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                job_role VARCHAR(255) NOT NULL,
                package_lpa NUMERIC(5,2) NOT NULL DEFAULT 0,
                eligibility_cgpa NUMERIC(4,2) NOT NULL DEFAULT 0,
                date DATE NOT NULL DEFAULT CURRENT_DATE,
                status VARCHAR(50) DEFAULT 'upcoming'
                    CHECK (status IN ('upcoming', 'active', 'completed'))
            );
        ''')
        # migrate drive_date → date
        if _col_exists(cur, "placement_drives", "drive_date") and not _col_exists(cur, "placement_drives", "date"):
            cur.execute("ALTER TABLE placement_drives RENAME COLUMN drive_date TO date;")
        elif not _col_exists(cur, "placement_drives", "date"):
            cur.execute("ALTER TABLE placement_drives ADD COLUMN date DATE NOT NULL DEFAULT CURRENT_DATE;")

        for col, defn in [
            ("package_lpa", "NUMERIC(5,2) NOT NULL DEFAULT 0"),
            ("eligibility_cgpa", "NUMERIC(4,2) NOT NULL DEFAULT 0"),
            ("status", "VARCHAR(50) DEFAULT 'upcoming'"),
            ("description", "TEXT"),
        ]:
            if not _col_exists(cur, "placement_drives", col):
                cur.execute(f"ALTER TABLE placement_drives ADD COLUMN {col} {defn};")

        # ── 15. Drive Applications ────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS drive_applications (
                id SERIAL PRIMARY KEY,
                drive_id INTEGER REFERENCES placement_drives(id) ON DELETE CASCADE,
                student_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                status VARCHAR(50) DEFAULT 'applied'
                    CHECK (status IN ('applied', 'shortlisted', 'selected', 'rejected')),
                UNIQUE(drive_id, student_id)
            );
        ''')

        # ── 16. Interview Feedback ────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS interview_feedback (
                id SERIAL PRIMARY KEY,
                application_id INTEGER REFERENCES drive_applications(id) ON DELETE CASCADE,
                round_name VARCHAR(255) NOT NULL,
                interviewer_name VARCHAR(255) NOT NULL,
                rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                comments TEXT
            );
        ''')

        # ── Seed: MITADT UNIVERSITY ───────────────────────────────────────────
        cur.execute('''
            INSERT INTO colleges (id, name, location)
            VALUES (1, 'MITADT UNIVERSITY', 'Pune')
            ON CONFLICT (id) DO NOTHING;
        ''')

        print("✅ Database schema successfully checked / initialized.")
