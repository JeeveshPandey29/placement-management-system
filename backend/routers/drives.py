from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_db
from auth import require_admin, require_trainer, require_student, get_current_user
from schemas import (
    PlacementDriveCreate, PlacementDriveUpdate, PlacementDriveOut,
    DriveApplicationOut, FeedbackCreate, FeedbackOut
)
import psycopg2

router = APIRouter()


def _send_notification(cur, title: str, message: str, target_type: str,
                        target_id: int, created_by: int):
    cur.execute(
        "INSERT INTO notifications (title, message, target_type, target_id, created_by) "
        "VALUES (%s, %s, %s, %s, %s)",
        (title, message, target_type, target_id, created_by)
    )


# ── Create drive ──────────────────────────────────────────────────────────────
@router.post("", response_model=PlacementDriveOut, status_code=status.HTTP_201_CREATED)
def create_drive(payload: PlacementDriveCreate, admin: dict = Depends(require_admin)):
    with get_db() as cur:
        cur.execute(
            "INSERT INTO placement_drives "
            "(company_name, job_role, description, package_lpa, eligibility_cgpa, date, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (payload.company_name, payload.job_role, payload.description,
             payload.package_lpa, payload.eligibility_cgpa, payload.date, payload.status)
        )
        did = cur.fetchone()[0]
    return {"id": did, "company_name": payload.company_name, "job_role": payload.job_role,
            "description": payload.description, "package_lpa": payload.package_lpa,
            "eligibility_cgpa": payload.eligibility_cgpa, "date": payload.date, "status": payload.status}


# ── Edit drive ────────────────────────────────────────────────────────────────
@router.put("/{drive_id}", response_model=PlacementDriveOut)
def update_drive(drive_id: int, payload: PlacementDriveUpdate, admin: dict = Depends(require_admin)):
    fields, vals = [], []
    for k, v in payload.model_dump(exclude_none=True).items():
        fields.append(f"{k} = %s"); vals.append(v)
    if not fields:
        raise HTTPException(status_code=400, detail="Nothing to update")
    vals.append(drive_id)
    with get_db() as cur:
        cur.execute(f"UPDATE placement_drives SET {', '.join(fields)} WHERE id = %s", vals)
        cur.execute(
            "SELECT id, company_name, job_role, description, package_lpa, eligibility_cgpa, date, status "
            "FROM placement_drives WHERE id = %s", (drive_id,)
        )
        r = cur.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Drive not found")
    return {"id": r[0], "company_name": r[1], "job_role": r[2], "description": r[3],
            "package_lpa": r[4], "eligibility_cgpa": r[5], "date": r[6], "status": r[7]}


# ── Delete drive ──────────────────────────────────────────────────────────────
@router.delete("/{drive_id}")
def delete_drive(drive_id: int, admin: dict = Depends(require_admin)):
    with get_db() as cur:
        cur.execute("DELETE FROM placement_drives WHERE id = %s RETURNING id", (drive_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Drive not found")
    return {"message": "Drive deleted"}


# ── List drives ───────────────────────────────────────────────────────────────
@router.get("", response_model=List[PlacementDriveOut])
def list_drives(current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute(
            "SELECT id, company_name, job_role, description, package_lpa, eligibility_cgpa, date, status "
            "FROM placement_drives ORDER BY date ASC"
        )
        rows = cur.fetchall()
    return [{"id": r[0], "company_name": r[1], "job_role": r[2], "description": r[3],
             "package_lpa": r[4], "eligibility_cgpa": r[5], "date": r[6], "status": r[7]}
            for r in rows]


# ── Check eligibility for a drive (student) ───────────────────────────────────
@router.get("/{drive_id}/eligibility")
def check_eligibility(drive_id: int, student: dict = Depends(require_student)):
    with get_db() as cur:
        cur.execute(
            "SELECT eligibility_cgpa FROM placement_drives WHERE id = %s", (drive_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Drive not found")
        required = float(row[0])
        cur.execute(
            "SELECT gpa FROM student_profiles WHERE user_id = %s", (student["id"],)
        )
        srow = cur.fetchone()
        student_gpa = float(srow[0]) if srow and srow[0] else 0.0
        # Check if already applied
        cur.execute(
            "SELECT id, status FROM drive_applications WHERE drive_id=%s AND student_id=%s",
            (drive_id, student["id"])
        )
        app = cur.fetchone()
    return {
        "eligible": student_gpa >= required,
        "student_gpa": student_gpa,
        "required_cgpa": required,
        "applied": app is not None,
        "application_status": app[1] if app else None,
        "application_id": app[0] if app else None
    }


# ── Get my applied drive IDs ──────────────────────────────────────────────────
@router.get("/my/applied-ids")
def get_my_applied_ids(student: dict = Depends(require_student)):
    with get_db() as cur:
        cur.execute(
            "SELECT drive_id, status FROM drive_applications WHERE student_id = %s",
            (student["id"],)
        )
        rows = cur.fetchall()
    return {str(r[0]): r[1] for r in rows}


# ── Apply for drive ───────────────────────────────────────────────────────────
@router.post("/{drive_id}/apply", response_model=DriveApplicationOut,
             status_code=status.HTTP_201_CREATED)
def apply_for_drive(drive_id: int, current_user: dict = Depends(require_student)):
    student_id = current_user["id"]
    with get_db() as cur:
        cur.execute(
            "SELECT company_name, job_role, eligibility_cgpa FROM placement_drives WHERE id = %s",
            (drive_id,)
        )
        drive_row = cur.fetchone()
        if not drive_row:
            raise HTTPException(status_code=404, detail="Drive not found")
        company_name, job_role, eligibility_cgpa = drive_row

        cur.execute("SELECT gpa FROM student_profiles WHERE user_id = %s", (student_id,))
        srow = cur.fetchone()
        if not srow or srow[0] is None:
            raise HTTPException(status_code=400, detail="Complete your profile with GPA before applying.")
        if float(srow[0]) < float(eligibility_cgpa):
            raise HTTPException(
                status_code=400,
                detail=f"Ineligible. Required CGPA: {eligibility_cgpa}, Yours: {srow[0]}"
            )

        try:
            cur.execute(
                "INSERT INTO drive_applications (drive_id, student_id, status) "
                "VALUES (%s, %s, 'applied') RETURNING id, status",
                (drive_id, student_id)
            )
            app_id, app_status = cur.fetchone()
        except psycopg2.errors.UniqueViolation:
            raise HTTPException(status_code=400, detail="Already applied.")

        # Auto-notify student
        _send_notification(
            cur,
            f"Application Submitted — {company_name}",
            f"You have successfully applied for {job_role} at {company_name}. We'll notify you of updates.",
            "student", student_id, student_id
        )

    return {"id": app_id, "drive_id": drive_id, "company_name": company_name,
            "job_role": job_role, "student_id": student_id,
            "student_email": current_user["email"], "status": app_status}


# ── My applications ───────────────────────────────────────────────────────────
@router.get("/my/applications", response_model=List[DriveApplicationOut])
def get_my_applications(student: dict = Depends(require_student)):
    with get_db() as cur:
        cur.execute("""
            SELECT da.id, da.drive_id, pd.company_name, pd.job_role,
                   da.student_id, u.email, u.full_name, da.status
            FROM drive_applications da
            JOIN placement_drives pd ON da.drive_id = pd.id
            JOIN pms_users u ON da.student_id = u.id
            WHERE da.student_id = %s ORDER BY da.id DESC
        """, (student["id"],))
        rows = cur.fetchall()
    return [{"id": r[0], "drive_id": r[1], "company_name": r[2], "job_role": r[3],
             "student_id": r[4], "student_email": r[5], "student_name": r[6], "status": r[7]}
            for r in rows]


# ── Drive applications (trainer/admin) ────────────────────────────────────────
@router.get("/{drive_id}/applications", response_model=List[DriveApplicationOut])
def get_drive_applications(drive_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        if current_user["role"] == "student":
            cur.execute("""
                SELECT da.id, da.drive_id, pd.company_name, pd.job_role,
                       da.student_id, u.email, u.full_name, da.status
                FROM drive_applications da
                JOIN placement_drives pd ON da.drive_id = pd.id
                JOIN pms_users u ON da.student_id = u.id
                WHERE da.drive_id = %s AND da.student_id = %s
            """, (drive_id, current_user["id"]))
        else:
            cur.execute("""
                SELECT da.id, da.drive_id, pd.company_name, pd.job_role,
                       da.student_id, u.email, u.full_name, da.status
                FROM drive_applications da
                JOIN placement_drives pd ON da.drive_id = pd.id
                JOIN pms_users u ON da.student_id = u.id
                WHERE da.drive_id = %s ORDER BY u.full_name
            """, (drive_id,))
        rows = cur.fetchall()
    return [{"id": r[0], "drive_id": r[1], "company_name": r[2], "job_role": r[3],
             "student_id": r[4], "student_email": r[5], "student_name": r[6], "status": r[7]}
            for r in rows]


# ── Update application status + auto-notify ───────────────────────────────────
@router.put("/applications/{application_id}/status")
def update_application_status(application_id: int, status_val: str,
                               trainer: dict = Depends(require_trainer)):
    if status_val not in ("applied", "shortlisted", "selected", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")
    with get_db() as cur:
        cur.execute(
            "SELECT da.student_id, pd.company_name, pd.job_role "
            "FROM drive_applications da "
            "JOIN placement_drives pd ON da.drive_id = pd.id "
            "WHERE da.id = %s",
            (application_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")
        student_id, company_name, job_role = row

        cur.execute("UPDATE drive_applications SET status = %s WHERE id = %s",
                    (status_val, application_id))

        if status_val == "selected":
            cur.execute("UPDATE student_profiles SET status = 'placed' WHERE user_id = %s",
                        (student_id,))

        # Status labels for notification
        label_map = {
            "shortlisted": "Shortlisted 🎉",
            "selected": "Selected — Congratulations! 🏆",
            "rejected": "Not Selected",
            "applied": "Application Received"
        }
        _send_notification(
            cur,
            f"{company_name} — {label_map.get(status_val, status_val)}",
            f"Your application for {job_role} at {company_name} has been updated to: {status_val.upper()}.",
            "student", student_id, trainer["id"]
        )
    return {"message": "Status updated", "status": status_val}


# ── Interview feedback ────────────────────────────────────────────────────────
@router.post("/applications/{application_id}/feedback",
             response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def leave_feedback(application_id: int, payload: FeedbackCreate,
                   trainer: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute("""
            SELECT da.student_id, u.email, pd.company_name
            FROM drive_applications da
            JOIN pms_users u ON da.student_id = u.id
            JOIN placement_drives pd ON da.drive_id = pd.id
            WHERE da.id = %s
        """, (application_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")
        student_id, student_email, company_name = row
        cur.execute(
            "INSERT INTO interview_feedback "
            "(application_id, round_name, interviewer_name, rating, comments) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (application_id, payload.round_name, payload.interviewer_name,
             payload.rating, payload.comments)
        )
        fid = cur.fetchone()[0]
    return {"id": fid, "application_id": application_id, "company_name": company_name,
            "student_id": student_id, "student_email": student_email,
            "round_name": payload.round_name, "interviewer_name": payload.interviewer_name,
            "rating": payload.rating, "comments": payload.comments}


@router.get("/applications/{application_id}/feedback", response_model=List[FeedbackOut])
def view_feedback(application_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute("SELECT student_id FROM drive_applications WHERE id = %s", (application_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")
        if current_user["role"] == "student" and current_user["id"] != row[0]:
            raise HTTPException(status_code=403, detail="Access denied")
        cur.execute("""
            SELECT f.id, f.application_id, pd.company_name, da.student_id,
                   u.email, f.round_name, f.interviewer_name, f.rating, f.comments
            FROM interview_feedback f
            JOIN drive_applications da ON f.application_id = da.id
            JOIN pms_users u ON da.student_id = u.id
            JOIN placement_drives pd ON da.drive_id = pd.id
            WHERE f.application_id = %s ORDER BY f.id
        """, (application_id,))
        rows = cur.fetchall()
    return [{"id": r[0], "application_id": r[1], "company_name": r[2], "student_id": r[3],
             "student_email": r[4], "round_name": r[5], "interviewer_name": r[6],
             "rating": r[7], "comments": r[8]} for r in rows]
