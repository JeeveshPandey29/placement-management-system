from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal

# Authentication Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str = Field(..., pattern="^(admin|trainer|student)$")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str


class CollegeOut(BaseModel):
    id: int
    name: str
    location: str

# Student Profile Schemas
class StudentProfileUpdate(BaseModel):
    roll_number: Optional[str] = None
    college_id: Optional[int] = None
    branch: Optional[str] = None
    gpa: Optional[Decimal] = None
    resume_url: Optional[str] = None
    skills: Optional[str] = None  # Comma-separated list of skills
    status: Optional[str] = Field(None, pattern="^(unplaced|placed)$")

class StudentProfileOut(BaseModel):
    user_id: int
    email: str
    roll_number: Optional[str] = None
    college_id: Optional[int] = None
    college_name: Optional[str] = None
    branch: Optional[str] = None
    gpa: Optional[Decimal] = None
    resume_url: Optional[str] = None
    skills: Optional[str] = None
    status: str

# Attendance Schemas
class AttendanceRecord(BaseModel):
    student_id: int
    date: date
    status: str = Field(..., pattern="^(present|absent|late)$")
    session_name: str

class AttendanceOut(BaseModel):
    id: int
    student_id: int
    student_email: str
    date: date
    status: str
    session_name: str

# Assessment Schemas
class AssessmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    max_score: int
    date: date

class AssessmentOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    max_score: int
    date: date

class ScoreCreate(BaseModel):
    student_id: int
    score: Decimal
    feedback: Optional[str] = None

class ScoreOut(BaseModel):
    id: int
    assessment_id: int
    student_id: int
    student_email: str
    score: Decimal
    feedback: Optional[str] = None

# Placement Drive Schemas
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
    status: str

# Interview Feedback Schemas
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

# Analytics / Dashboard Schemas
class AnalyticsSummary(BaseModel):
    total_students: int
    placed_students: int
    placement_percentage: float
    average_gpa: float
    total_drives: int
    total_colleges: int
