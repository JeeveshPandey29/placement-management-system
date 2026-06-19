import os
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv
import psycopg2

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

# Initialize Connection Pool
pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL,
)

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

        # 2. PMS Users (Auth credentials + Role) — named pms_users to avoid clash with Supabase auth.users
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pms_users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'student' CHECK (role IN ('admin', 'trainer', 'student'))
            );
        ''')

        # 3. Student Profiles (Linked to pms_users & College)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS student_profiles (
                user_id INTEGER PRIMARY KEY REFERENCES pms_users(id) ON DELETE CASCADE,
                roll_number VARCHAR(100),
                college_id INTEGER REFERENCES colleges(id) ON DELETE SET NULL,
                branch VARCHAR(100),
                gpa NUMERIC(4,2) DEFAULT 0.00,
                resume_url TEXT,
                skills TEXT,
                status VARCHAR(50) DEFAULT 'unplaced' CHECK (status IN ('unplaced', 'placed'))
            );
        ''')

        # 4. Attendance
        cur.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                date DATE NOT NULL,
                status VARCHAR(50) NOT NULL CHECK (status IN ('present', 'absent', 'late')),
                session_name VARCHAR(255) NOT NULL
            );
        ''')

        # 5. Assessments
        cur.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                max_score INTEGER NOT NULL,
                date DATE NOT NULL
            );
        ''')

        # 6. Assessment Scores
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

        # 7. Placement Drives
        cur.execute('''
            CREATE TABLE IF NOT EXISTS placement_drives (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                job_role VARCHAR(255) NOT NULL,
                package_lpa NUMERIC(5,2) NOT NULL,
                eligibility_cgpa NUMERIC(4,2) NOT NULL,
                date DATE NOT NULL,
                status VARCHAR(50) DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'active', 'completed'))
            );
        ''')

        # 8. Drive Applications
        cur.execute('''
            CREATE TABLE IF NOT EXISTS drive_applications (
                id SERIAL PRIMARY KEY,
                drive_id INTEGER REFERENCES placement_drives(id) ON DELETE CASCADE,
                student_id INTEGER REFERENCES pms_users(id) ON DELETE CASCADE,
                status VARCHAR(50) DEFAULT 'applied' CHECK (status IN ('applied', 'shortlisted', 'selected', 'rejected')),
                UNIQUE(drive_id, student_id)
            );
        ''')

        # 9. Interview Feedback
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

        # 10. Seed MITADT UNIVERSITY
        cur.execute('''
            INSERT INTO colleges (id, name, location)
            VALUES (1, 'MITADT UNIVERSITY', 'Pune')
            ON CONFLICT (id) DO NOTHING;
        ''')
        print("Database schema successfully checked / initialized.")
