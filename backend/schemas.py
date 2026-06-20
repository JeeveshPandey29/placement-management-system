from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import date, time
from decimal import Decimal

# ── Auth ──────────────────────────────────────────────────────────────────────
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    full_name: Optional[str] = None
    must_change_password: bool = False

class SetPasswordIn(BaseModel):
    new_password: str = Field(..., min_length=6)

class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

class CreateUserIn(BaseModel):
    email: EmailStr
    full_name: str
    role: str = Field(..., pattern="^(admin|trainer|student)$")
    enrollment_number: Optional[str] = None
    branch: Optional[str] = None

class AdminSetupIn(BaseModel):
    email: EmailStr
    password: str
    full_name: str

# ── Colleges ──────────────────────────────────────────────────────────────────
class CollegeCreate(BaseModel):
    name: str
    location: str

class CollegeOut(BaseModel):
    id: int
    name: str
    location: str

# ── Batches ───────────────────────────────────────────────────────────────────
class BatchCreate(BaseModel):
    name: str
    branch: Optional[str] = None
    trainer_id: Optional[int] = None

class BatchUpdate(BaseModel):
    name: Optional[str] = None
    branch: Optional[str] = None
    trainer_id: Optional[int] = None  # send null to unassign

class BatchOut(BaseModel):
    id: int
    name: str
    branch: Optional[str] = None
    trainer_id: Optional[int] = None
    trainer_name: Optional[str] = None
    student_count: int = 0

class BatchStudentIn(BaseModel):
    student_ids: List[int]

# ── Classes ───────────────────────────────────────────────────────────────────
class ClassCreate(BaseModel):
    batch_id: int
    title: str
    description: Optional[str] = None
    class_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None

class ClassUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    class_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None

class ClassOut(BaseModel):
    id: int
    batch_id: int
    batch_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    class_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None

# ── Notifications ─────────────────────────────────────────────────────────────
class NotificationCreate(BaseModel):
    title: str
    message: str
    target_type: str = Field("all", pattern="^(all|batch|student)$")
    target_id: Optional[int] = None

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    target_type: str
    target_id: Optional[int] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: Optional[str] = None
    is_read: bool = False

# ── Student Profiles ──────────────────────────────────────────────────────────
class StudentProfileUpdate(BaseModel):
    enrollment_number: Optional[str] = None
    roll_number: Optional[str] = None
    college_id: Optional[int] = None
    branch: Optional[str] = None
    gpa: Optional[Decimal] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    address: Optional[str] = None
    resume_summary: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[Any] = None
    projects: Optional[Any] = None
    certifications: Optional[Any] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_url: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(unplaced|placed)$")

class StudentProfileOut(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str] = None
    enrollment_number: Optional[str] = None
    roll_number: Optional[str] = None
    college_id: Optional[int] = None
    college_name: Optional[str] = None
    branch: Optional[str] = None
    gpa: Optional[Decimal] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    address: Optional[str] = None
    resume_summary: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[Any] = None
    projects: Optional[Any] = None
    certifications: Optional[Any] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_url: Optional[str] = None
    status: str
    batch_name: Optional[str] = None

# ── Attendance ────────────────────────────────────────────────────────────────
class AttendanceRecord(BaseModel):
    student_id: int
    date: date
    status: str = Field(..., pattern="^(present|absent|late)$")
    session_name: str
    batch_id: Optional[int] = None
    class_id: Optional[int] = None

class BulkAttendanceRecord(BaseModel):
    batch_id: int
    date: date
    session_name: str
    records: List[dict]  # [{student_id, status}]

class AttendanceOut(BaseModel):
    id: int
    student_id: int
    student_email: str
    student_name: Optional[str] = None
    date: date
    status: str
    session_name: str
    batch_id: Optional[int] = None
    class_id: Optional[int] = None

# ── Assessments ───────────────────────────────────────────────────────────────
class AssessmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    max_score: int
    date: date
    batch_id: Optional[int] = None

class AssessmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    max_score: Optional[int] = None
    date: Optional[date] = None
    batch_id: Optional[int] = None

class AssessmentOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    max_score: int
    date: date
    batch_id: Optional[int] = None
    batch_name: Optional[str] = None

class ScoreCreate(BaseModel):
    student_id: int
    score: Decimal
    feedback: Optional[str] = None

class ScoreOut(BaseModel):
    id: int
    assessment_id: int
    student_id: int
    student_email: str
    student_name: Optional[str] = None
    score: Decimal
    feedback: Optional[str] = None

# ── Placement Drives ──────────────────────────────────────────────────────────
class PlacementDriveCreate(BaseModel):
    company_name: str
    job_role: str
    description: Optional[str] = None
    package_lpa: Decimal
    eligibility_cgpa: Decimal
    date: date
    status: str = Field("upcoming", pattern="^(upcoming|active|completed)$")

class PlacementDriveUpdate(BaseModel):
    company_name: Optional[str] = None
    job_role: Optional[str] = None
    description: Optional[str] = None
    package_lpa: Optional[Decimal] = None
    eligibility_cgpa: Optional[Decimal] = None
    date: Optional[date] = None
    status: Optional[str] = Field(None, pattern="^(upcoming|active|completed)$")

class PlacementDriveOut(BaseModel):
    id: int
    company_name: str
    job_role: str
    description: Optional[str] = None
    package_lpa: Decimal
    eligibility_cgpa: Decimal
    date: date
    status: str

class DriveApplicationOut(BaseModel):
    id: int
    drive_id: int
    company_name: str
    job_role: str
    student_id: int
    student_email: str
    student_name: Optional[str] = None
    status: str

class FeedbackCreate(BaseModel):
    round_name: str
    interviewer_name: str
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None

class FeedbackOut(BaseModel):
    id: int
    application_id: int
    company_name: str
    student_id: int
    student_email: str
    round_name: str
    interviewer_name: str
    rating: int
    comments: Optional[str] = None

# ── Analytics ─────────────────────────────────────────────────────────────────
class AnalyticsSummary(BaseModel):
    total_students: int
    placed_students: int
    placement_percentage: float
    average_gpa: float
    total_drives: int
    total_colleges: int
    total_batches: int


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    full_name: Optional[str] = None
    must_change_password: bool = False

class SetPasswordIn(BaseModel):
    new_password: str = Field(..., min_length=6)

class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

# ── Admin User Management ─────────────────────────────────────────────────────
class CreateUserIn(BaseModel):
    email: EmailStr
    full_name: str
    role: str = Field(..., pattern="^(admin|trainer|student)$")
    enrollment_number: Optional[str] = None   # for students
    branch: Optional[str] = None              # for students

class AdminSetupIn(BaseModel):
    email: EmailStr
    password: str
    full_name: str

# ── Colleges ──────────────────────────────────────────────────────────────────
class CollegeCreate(BaseModel):
    name: str
    location: str

class CollegeOut(BaseModel):
    id: int
    name: str
    location: str

# ── Batches ───────────────────────────────────────────────────────────────────
class BatchCreate(BaseModel):
    name: str
    branch: Optional[str] = None
    trainer_id: Optional[int] = None

class BatchUpdate(BaseModel):
    name: Optional[str] = None
    branch: Optional[str] = None
    trainer_id: Optional[int] = None

class BatchOut(BaseModel):
    id: int
    name: str
    branch: Optional[str] = None
    trainer_id: Optional[int] = None
    trainer_name: Optional[str] = None
    student_count: int = 0

class BatchStudentIn(BaseModel):
    student_ids: List[int]

# ── Classes ───────────────────────────────────────────────────────────────────
class ClassCreate(BaseModel):
    batch_id: int
    title: str
    description: Optional[str] = None
    class_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None

class ClassOut(BaseModel):
    id: int
    batch_id: int
    batch_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    class_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None

# ── Notifications ─────────────────────────────────────────────────────────────
class NotificationCreate(BaseModel):
    title: str
    message: str
    target_type: str = Field("all", pattern="^(all|batch|student)$")
    target_id: Optional[int] = None

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    target_type: str
    target_id: Optional[int] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: Optional[str] = None
    is_read: bool = False

# ── Student Profiles ──────────────────────────────────────────────────────────
class StudentProfileUpdate(BaseModel):
    enrollment_number: Optional[str] = None
    roll_number: Optional[str] = None
    college_id: Optional[int] = None
    branch: Optional[str] = None
    gpa: Optional[Decimal] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    address: Optional[str] = None
    resume_summary: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[Any] = None       # JSON list
    projects: Optional[Any] = None        # JSON list
    certifications: Optional[Any] = None  # JSON list
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_url: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(unplaced|placed)$")

class StudentProfileOut(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str] = None
    enrollment_number: Optional[str] = None
    roll_number: Optional[str] = None
    college_id: Optional[int] = None
    college_name: Optional[str] = None
    branch: Optional[str] = None
    gpa: Optional[Decimal] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    address: Optional[str] = None
    resume_summary: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[Any] = None
    projects: Optional[Any] = None
    certifications: Optional[Any] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_url: Optional[str] = None
    status: str
    batch_name: Optional[str] = None

# ── Attendance ────────────────────────────────────────────────────────────────
class AttendanceRecord(BaseModel):
    student_id: int
    date: date
    status: str = Field(..., pattern="^(present|absent|late)$")
    session_name: str
    batch_id: Optional[int] = None
    class_id: Optional[int] = None

class AttendanceOut(BaseModel):
    id: int
    student_id: int
    student_email: str
    student_name: Optional[str] = None
    date: date
    status: str
    session_name: str
    batch_id: Optional[int] = None
    class_id: Optional[int] = None

# ── Assessments ───────────────────────────────────────────────────────────────
class AssessmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    max_score: int
    date: date
    batch_id: Optional[int] = None

class AssessmentOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    max_score: int
    date: date
    batch_id: Optional[int] = None
    batch_name: Optional[str] = None

class ScoreCreate(BaseModel):
    student_id: int
    score: Decimal
    feedback: Optional[str] = None

class ScoreOut(BaseModel):
    id: int
    assessment_id: int
    student_id: int
    student_email: str
    student_name: Optional[str] = None
    score: Decimal
    feedback: Optional[str] = None

# ── Placement Drives ──────────────────────────────────────────────────────────
class PlacementDriveCreate(BaseModel):
    company_name: str
    job_role: str
    package_lpa: Decimal
    eligibility_cgpa: Decimal
    date: date
    status: str = Field("upcoming", pattern="^(upcoming|active|completed)$")

class PlacementDriveOut(BaseModel):
    id: int
    company_name: str
    job_role: str
    package_lpa: Decimal
    eligibility_cgpa: Decimal
    date: date
    status: str

class DriveApplicationOut(BaseModel):
    id: int
    drive_id: int
    company_name: str
    job_role: str
    student_id: int
    student_email: str
    student_name: Optional[str] = None
    status: str

class FeedbackCreate(BaseModel):
    round_name: str
    interviewer_name: str
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None

class FeedbackOut(BaseModel):
    id: int
    application_id: int
    company_name: str
    student_id: int
    student_email: str
    round_name: str
    interviewer_name: str
    rating: int
    comments: Optional[str] = None

# ── Analytics ─────────────────────────────────────────────────────────────────
class AnalyticsSummary(BaseModel):
    total_students: int
    placed_students: int
    placement_percentage: float
    average_gpa: float
    total_drives: int
    total_colleges: int
    total_batches: int
