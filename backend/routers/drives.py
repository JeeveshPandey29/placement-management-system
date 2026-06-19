from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_db
from auth import require_admin, require_trainer, require_student, get_current_user
from schemas import (
    PlacementDriveCreate,
    PlacementDriveOut,
    DriveApplicationOut,
    FeedbackCreate,
    FeedbackOut
)
import psycopg2

router = APIRouter()

# ==========================================
# PLACEMENT DRIVES
# ==========================================

@router.post("", response_model=PlacementDriveOut, status_code=status.HTTP_201_CREATED)
def create_placement_drive(payload: PlacementDriveCreate, admin_user: dict = Depends(require_admin)):
    try:
        with get_db() as cur:
            cur.execute(
                """INSERT INTO placement_drives (company_name, job_role, package_lpa, eligibility_cgpa, date, status)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (payload.company_name, payload.job_role, payload.package_lpa, payload.eligibility_cgpa, payload.date, payload.status)
            )
            drive_id = cur.fetchone()[0]
        return {
            "id": drive_id,
            "company_name": payload.company_name,
            "job_role": payload.job_role,
            "package_lpa": payload.package_lpa,
            "eligibility_cgpa": payload.eligibility_cgpa,
            "date": payload.date,
            "status": payload.status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[PlacementDriveOut])
def list_placement_drives(current_user: dict = Depends(get_current_user)):
    try:
        with get_db() as cur:
            cur.execute("SELECT id, company_name, job_role, package_lpa, eligibility_cgpa, date, status FROM placement_drives ORDER BY date ASC")
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "company_name": r[1],
                    "job_role": r[2],
                    "package_lpa": r[3],
                    "eligibility_cgpa": r[4],
                    "date": r[5],
                    "status": r[6]
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# APPLICATIONS
# ==========================================

@router.post("/{drive_id}/apply", response_model=DriveApplicationOut, status_code=status.HTTP_201_CREATED)
def apply_for_placement_drive(drive_id: int, current_user: dict = Depends(require_student)):
    try:
        student_id = current_user["id"]
        with get_db() as cur:
            # Fetch drive eligibility criteria
            cur.execute("SELECT company_name, job_role, eligibility_cgpa FROM placement_drives WHERE id = %s", (drive_id,))
            drive_row = cur.fetchone()
            if not drive_row:
                raise HTTPException(status_code=404, detail="Placement drive not found")
            company_name, job_role, eligibility_cgpa = drive_row[0], drive_row[1], drive_row[2]

            # Fetch student GPA
            cur.execute("SELECT gpa, college_id FROM student_profiles WHERE user_id = %s", (student_id,))
            student_row = cur.fetchone()
            if not student_row or student_row[0] is None:
                raise HTTPException(status_code=400, detail="Student GPA and profile details must be completed before applying.")
            student_gpa = student_row[0]

            # Enforce eligibility
            if student_gpa < eligibility_cgpa:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ineligible to apply. Required CGPA: {eligibility_cgpa}, Your CGPA: {student_gpa}"
                )

            # Insert application
            try:
                cur.execute(
                    """INSERT INTO drive_applications (drive_id, student_id, status)
                       VALUES (%s, %s, %s) RETURNING id, status""",
                    (drive_id, student_id, "applied")
                )
                app_id, app_status = cur.fetchone()
            except psycopg2.errors.UniqueViolation:
                raise HTTPException(status_code=400, detail="You have already applied for this placement drive.")

        return {
            "id": app_id,
            "drive_id": drive_id,
            "company_name": company_name,
            "job_role": job_role,
            "student_id": student_id,
            "student_email": current_user["email"],
            "status": app_status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my/applications", response_model=List[DriveApplicationOut])
def get_my_applications(current_user: dict = Depends(require_student)):
    try:
        student_id = current_user["id"]
        with get_db() as cur:
            cur.execute(
                """SELECT da.id, da.drive_id, pd.company_name, pd.job_role, da.student_id, u.email, da.status
                   FROM drive_applications da
                   JOIN placement_drives pd ON da.drive_id = pd.id
                   JOIN users u ON da.student_id = u.id
                   WHERE da.student_id = %s
                   ORDER BY da.id DESC""",
                (student_id,)
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "drive_id": r[1],
                    "company_name": r[2],
                    "job_role": r[3],
                    "student_id": r[4],
                    "student_email": r[5],
                    "status": r[6]
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{drive_id}/applications", response_model=List[DriveApplicationOut])
def get_drive_applications(drive_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_db() as cur:
            # Enforce: students can only see their own application. Admin/Trainers can see all.
            if current_user["role"] == "student":
                cur.execute(
                    """SELECT da.id, da.drive_id, pd.company_name, pd.job_role, da.student_id, u.email, da.status
                       FROM drive_applications da
                       JOIN placement_drives pd ON da.drive_id = pd.id
                       JOIN users u ON da.student_id = u.id
                       WHERE da.drive_id = %s AND da.student_id = %s""",
                    (drive_id, current_user["id"])
                )
            else:
                cur.execute(
                    """SELECT da.id, da.drive_id, pd.company_name, pd.job_role, da.student_id, u.email, da.status
                       FROM drive_applications da
                       JOIN placement_drives pd ON da.drive_id = pd.id
                       JOIN users u ON da.student_id = u.id
                       WHERE da.drive_id = %s""",
                    (drive_id,)
                )
                
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "drive_id": r[1],
                    "company_name": r[2],
                    "job_role": r[3],
                    "student_id": r[4],
                    "student_email": r[5],
                    "status": r[6]
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/applications/{application_id}/status")
def update_application_status(application_id: int, status_val: str, trainer_user: dict = Depends(require_trainer)):
    if status_val not in ("applied", "shortlisted", "selected", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status value")
        
    try:
        with get_db() as cur:
            # Check application exists
            cur.execute("SELECT student_id FROM drive_applications WHERE id = %s", (application_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Application not found")
            student_id = row[0]
            
            # Update application status
            cur.execute(
                "UPDATE drive_applications SET status = %s WHERE id = %s",
                (status_val, application_id)
            )
            
            # If student is selected (placed), update their student profile status to placed!
            if status_val == "selected":
                cur.execute(
                    "UPDATE student_profiles SET status = %s WHERE user_id = %s",
                    ("placed", student_id)
                )
                
        return {"message": "Application status updated successfully", "status": status_val}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# INTERVIEW FEEDBACK
# ==========================================

@router.post("/applications/{application_id}/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def leave_interview_feedback(application_id: int, payload: FeedbackCreate, trainer_user: dict = Depends(require_trainer)):
    try:
        with get_db() as cur:
            # Verify application exists and fetch details
            cur.execute(
                """SELECT da.student_id, u.email, pd.company_name
                   FROM drive_applications da
                   JOIN users u ON da.student_id = u.id
                   JOIN placement_drives pd ON da.drive_id = pd.id
                   WHERE da.id = %s""",
                (application_id,)
            )
            app_row = cur.fetchone()
            if not app_row:
                raise HTTPException(status_code=404, detail="Drive application not found")
            student_id, student_email, company_name = app_row[0], app_row[1], app_row[2]

            cur.execute(
                """INSERT INTO interview_feedback (application_id, round_name, interviewer_name, rating, comments)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (application_id, payload.round_name, payload.interviewer_name, payload.rating, payload.comments)
            )
            feedback_id = cur.fetchone()[0]

        return {
            "id": feedback_id,
            "application_id": application_id,
            "company_name": company_name,
            "student_id": student_id,
            "student_email": student_email,
            "round_name": payload.round_name,
            "interviewer_name": payload.interviewer_name,
            "rating": payload.rating,
            "comments": payload.comments
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/applications/{application_id}/feedback", response_model=List[FeedbackOut])
def view_interview_feedback(application_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_db() as cur:
            # Fetch application student owner
            cur.execute("SELECT student_id FROM drive_applications WHERE id = %s", (application_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Drive application not found")
            
            student_id = row[0]
            # Enforce student privacy
            if current_user["role"] == "student" and current_user["id"] != student_id:
                raise HTTPException(status_code=403, detail="You do not have access to this feedback.")

            cur.execute(
                """SELECT f.id, f.application_id, pd.company_name, da.student_id, u.email, f.round_name, f.interviewer_name, f.rating, f.comments
                   FROM interview_feedback f
                   JOIN drive_applications da ON f.application_id = da.id
                   JOIN users u ON da.student_id = u.id
                   JOIN placement_drives pd ON da.drive_id = pd.id
                   WHERE f.application_id = %s
                   ORDER BY f.id ASC""",
                (application_id,)
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "application_id": r[1],
                    "company_name": r[2],
                    "student_id": r[3],
                    "student_email": r[4],
                    "round_name": r[5],
                    "interviewer_name": r[6],
                    "rating": r[7],
                    "comments": r[8]
                }
                for r in rows
            ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
