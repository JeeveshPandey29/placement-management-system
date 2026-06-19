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

def init_db():
    with get_db() as cur:

        # 1. Colleges
        cur.execute('''
            CREATE TABLE IF NOT EXISTS colleges (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                location VARCHAR(255) NOT NULL
            );
        ''')

        # 2. PMS Users
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
        # safe ALTER for existing tables
        cur.execute("ALTER TABLE pms_users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);")
        cur.execute("ALTER TABLE pms_users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT FALSE;")
        cur.execute("ALTER TABLE pms_users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();")

        # 3. Student Profiles (extended)
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
                status VARCHAR(50) DEFAULT 'unplaced' CHECK (status IN ('unplaced', 'placed'))
            );
        ''')
        # safe ALTERs for existing deployments
        for col, defn in [
            ("enrollment_number", "VARCHAR(100)"),
            ("phone", "VARCHAR(20)"),
            ("dob", "DATE"),
            ("address", "TEXT"),
            ("resume_summary", "TEXT"),
            ("education", "JSONB DEFAULT '[]'::jsonb"),
            ("projects", "JSONB DEFAULT '[]'::jsonb"),
            ("certifications", "JSONB DEFAULT '[]'::jsonb"),
            ("linkedin_url", "TEXT"),
            ("github_url", "TEXT"),
            ("portfolio_url", "TEXT"),
        ]:
            cur.execute(f"ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS {col} {defn};")

        # 4. Batches
        cur.execute('''
            CREATE TABLE IF NOT EXISTS batches (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                branch VARCHAR(100),
                trainer_id INTEGER REFERENCES pms_users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        ''')

        # 5. Batch Students (many-to-many)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS batch_students (
                batch_id INTEGER REFERENCES batches(id) ON DELETE CASCADE,
                student_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                PRIMARY KEY (batch_id, student_id)
            );
        ''')

        # 6. Classes (sessions)
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

        # 7. Notifications
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

        # 8. Notification Reads
        cur.execute('''
            CREATE TABLE IF NOT EXISTS notification_reads (
                notification_id INTEGER REFERENCES notifications(id) ON DELETE CASCADE,
                student_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                read_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (notification_id, student_id)
            );
        ''')

        # 9. Password Reset Tokens
        cur.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                used BOOLEAN DEFAULT FALSE
            );
        ''')

        # 10. Attendance
        cur.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL,
                class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,
                date DATE NOT NULL,
                status VARCHAR(50) NOT NULL CHECK (status IN ('present', 'absent', 'late')),
                session_name VARCHAR(255) NOT NULL
            );
        ''')
        cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL;")
        cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL;")

        # 11. Assessments
        cur.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                max_score INTEGER NOT NULL,
                date DATE NOT NULL,
                batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL
            );
        ''')
        cur.execute("ALTER TABLE assessments ADD COLUMN IF NOT EXISTS batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL;")

        # 12. Assessment Scores
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

        # 13. Placement Drives
        cur.execute('''
            CREATE TABLE IF NOT EXISTS placement_drives (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                job_role VARCHAR(255) NOT NULL,
                package_lpa NUMERIC(5,2) NOT NULL,
                eligibility_cgpa NUMERIC(4,2) NOT NULL,
                date DATE NOT NULL,
                status VARCHAR(50) DEFAULT 'upcoming'
                    CHECK (status IN ('upcoming', 'active', 'completed'))
            );
        ''')

        # 14. Drive Applications
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

        # 15. Interview Feedback
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

        # Seed
        cur.execute('''
            INSERT INTO colleges (id, name, location)
            VALUES (1, 'MITADT UNIVERSITY', 'Pune')
            ON CONFLICT (id) DO NOTHING;
        ''')
        print("Database schema successfully checked / initialized.")
