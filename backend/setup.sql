-- ============================================================
-- PMS 3.0 — Complete Database Setup
-- Run this in Supabase SQL Editor after creating a new project
-- ============================================================

-- 1. Users
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Student' CHECK (role IN ('Admin', 'Trainer', 'Student')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Students
CREATE TABLE students (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    enrollment_no TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    batch_name TEXT NOT NULL,
    joining_date TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'PLACED', 'PASSED_OUT'))
);

-- 3. Trainers
CREATE TABLE trainers (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    specialization TEXT NOT NULL,
    experience_years INT NOT NULL,
    joining_date TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE'))
);

-- 4. Attendance
CREATE TABLE attendance (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
    attendance_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PRESENT', 'ABSENT', 'LATE')),
    remarks TEXT
);

-- 5. Assessments
CREATE TABLE assessments (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    assessment_date TEXT NOT NULL,
    total_marks INT NOT NULL,
    created_by BIGINT REFERENCES users(id)
);

-- 6. Assessment Results
CREATE TABLE assessment_results (
    id BIGSERIAL PRIMARY KEY,
    assessment_id BIGINT REFERENCES assessments(id) ON DELETE CASCADE,
    student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
    marks_obtained NUMERIC NOT NULL,
    grade TEXT NOT NULL,
    remarks TEXT,
    UNIQUE(assessment_id, student_id)
);

-- 7. Placement Drives
CREATE TABLE placement_drives (
    id BIGSERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    job_role TEXT NOT NULL,
    drive_date TEXT NOT NULL,
    location TEXT NOT NULL,
    eligibility_criteria TEXT,
    min_marks NUMERIC DEFAULT 0,
    package_lpa NUMERIC,
    status TEXT DEFAULT 'UPCOMING' CHECK (status IN ('UPCOMING', 'ONGOING', 'COMPLETED', 'CANCELLED'))
);

-- 8. Applications
CREATE TABLE applications (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
    placement_drive_id BIGINT REFERENCES placement_drives(id) ON DELETE CASCADE,
    application_date TEXT NOT NULL,
    status TEXT DEFAULT 'APPLIED' CHECK (status IN ('APPLIED', 'SHORTLISTED', 'SELECTED', 'REJECTED', 'WITHDRAWN')),
    UNIQUE(student_id, placement_drive_id)
);

-- 9. Interviews
CREATE TABLE interviews (
    id BIGSERIAL PRIMARY KEY,
    application_id BIGINT REFERENCES applications(id) ON DELETE CASCADE,
    interview_date TEXT NOT NULL,
    round_name TEXT NOT NULL,
    interviewer_name TEXT NOT NULL,
    status TEXT DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')),
    feedback TEXT
);

-- ============================================================
-- NEW TABLES FOR 5 NEW FEATURES
-- ============================================================

-- 10. Announcements
CREATE TABLE announcements (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_by BIGINT REFERENCES users(id),
    target_role TEXT DEFAULT 'ALL' CHECK (target_role IN ('ALL', 'Student', 'Trainer', 'Admin')),
    priority TEXT DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Offers
CREATE TABLE offers (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
    placement_drive_id BIGINT REFERENCES placement_drives(id),
    company_name TEXT NOT NULL,
    job_role TEXT NOT NULL,
    ctc_lpa NUMERIC NOT NULL,
    offer_date TEXT NOT NULL,
    joining_date TEXT,
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ACCEPTED', 'DECLINED')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES for performance
-- ============================================================
CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_attendance_student ON attendance(student_id);
CREATE INDEX idx_results_student ON assessment_results(student_id);
CREATE INDEX idx_results_assessment ON assessment_results(assessment_id);
CREATE INDEX idx_applications_student ON applications(student_id);
CREATE INDEX idx_applications_drive ON applications(placement_drive_id);
CREATE INDEX idx_offers_student ON offers(student_id);
CREATE INDEX idx_announcements_role ON announcements(target_role);

-- ============================================================
-- Disable RLS (since we use JWT auth in FastAPI, not Supabase auth)
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE trainers ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE placement_drives ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;
ALTER TABLE offers ENABLE ROW LEVEL SECURITY;

-- Allow service_role key to bypass RLS
CREATE POLICY "Allow all for service role" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service role" ON students FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service role" ON trainers FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service role" ON attendance FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service role" ON assessments FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service role" ON assessment_results FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service role" ON placement_drives FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service role" ON applications FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service role" ON interviews FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service role" ON announcements FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for service role" ON offers FOR ALL USING (true) WITH CHECK (true);
