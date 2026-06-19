import json
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_db
from auth import require_student, require_trainer, require_admin, get_current_user
from schemas import StudentProfileUpdate, StudentProfileOut

router = APIRouter()


def _row_to_profile(r) -> dict:
    def parse_json(v):
        if v is None:
            return []
        if isinstance(v, (list, dict)):
            return v
        try:
            return json.loads(v)
        except Exception:
            return []

    return {
        "user_id": r[0], "email": r[1], "full_name": r[2],
        "enrollment_number": r[3], "roll_number": r[4],
        "college_id": r[5], "college_name": r[6], "branch": r[7],
        "gpa": r[8], "phone": r[9], "dob": r[10], "address": r[11],
        "resume_summary": r[12], "skills": r[13],
        "education": parse_json(r[14]),
        "projects": parse_json(r[15]),
        "certifications": parse_json(r[16]),
        "linkedin_url": r[17], "github_url": r[18],
        "portfolio_url": r[19], "resume_url": r[20],
        "status": r[21] or "unplaced",
        "batch_name": r[22]
    }


PROFILE_SELECT = """
    SELECT sp.user_id, u.email, u.full_name,
           sp.enrollment_number, sp.roll_number,
           sp.college_id, c.name, sp.branch,
           sp.gpa, sp.phone, sp.dob, sp.address,
           sp.resume_summary, sp.skills,
           sp.education, sp.projects, sp.certifications,
           sp.linkedin_url, sp.github_url, sp.portfolio_url,
           sp.resume_url, sp.status,
           (SELECT b.name FROM batch_students bs
            JOIN batches b ON bs.batch_id = b.id
            WHERE bs.student_id = sp.user_id LIMIT 1) AS batch_name
    FROM student_profiles sp
    JOIN pms_users u ON sp.user_id = u.id
    LEFT JOIN colleges c ON sp.college_id = c.id
"""


# ── Student: get own profile ───────────────────────────────────────────────────
@router.get("/profile", response_model=StudentProfileOut)
def get_own_profile(current_user: dict = Depends(require_student)):
    with get_db() as cur:
        cur.execute(PROFILE_SELECT + " WHERE sp.user_id = %s", (current_user["id"],))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _row_to_profile(row)


# ── Student: update own profile ────────────────────────────────────────────────
@router.put("/profile", response_model=StudentProfileOut)
def update_own_profile(payload: StudentProfileUpdate,
                        current_user: dict = Depends(require_student)):
    uid = current_user["id"]
    fields, vals = [], []
    mapping = {
        "enrollment_number": payload.enrollment_number,
        "roll_number": payload.roll_number,
        "college_id": payload.college_id,
        "branch": payload.branch,
        "gpa": payload.gpa,
        "phone": payload.phone,
        "dob": payload.dob,
        "address": payload.address,
        "resume_summary": payload.resume_summary,
        "skills": payload.skills,
        "linkedin_url": payload.linkedin_url,
        "github_url": payload.github_url,
        "portfolio_url": payload.portfolio_url,
        "resume_url": payload.resume_url,
        "status": payload.status,
    }
    for k, v in mapping.items():
        if v is not None:
            fields.append(f"{k} = %s")
            vals.append(v)
    # JSON fields
    for k in ("education", "projects", "certifications"):
        v = getattr(payload, k)
        if v is not None:
            fields.append(f"{k} = %s")
            vals.append(json.dumps(v))
    if fields:
        vals.append(uid)
        with get_db() as cur:
            cur.execute(f"UPDATE student_profiles SET {', '.join(fields)} WHERE user_id = %s", vals)
    with get_db() as cur:
        cur.execute(PROFILE_SELECT + " WHERE sp.user_id = %s", (uid,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _row_to_profile(row)


# ── Trainer/Admin: list students ───────────────────────────────────────────────
@router.get("", response_model=List[StudentProfileOut])
def list_students(
    college_id: Optional[int] = None,
    status: Optional[str] = None,
    batch_id: Optional[int] = None,
    current_user: dict = Depends(require_trainer)
):
    conditions, vals = [], []
    if college_id:
        conditions.append("sp.college_id = %s"); vals.append(college_id)
    if status:
        conditions.append("sp.status = %s"); vals.append(status)
    if batch_id:
        conditions.append(
            "sp.user_id IN (SELECT student_id FROM batch_students WHERE batch_id = %s)"
        )
        vals.append(batch_id)
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    with get_db() as cur:
        cur.execute(PROFILE_SELECT + where + " ORDER BY u.full_name", vals)
        rows = cur.fetchall()
    return [_row_to_profile(r) for r in rows]


# ── Trainer/Admin: get student by id ──────────────────────────────────────────
@router.get("/{user_id}", response_model=StudentProfileOut)
def get_student_by_id(user_id: int, current_user: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute(PROFILE_SELECT + " WHERE sp.user_id = %s", (user_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return _row_to_profile(row)


# ── Admin: update student profile (admin override) ────────────────────────────
@router.put("/{user_id}", response_model=StudentProfileOut)
def admin_update_student(user_id: int, payload: StudentProfileUpdate,
                          admin: dict = Depends(require_admin)):
    fields, vals = [], []
    mapping = {
        "enrollment_number": payload.enrollment_number,
        "roll_number": payload.roll_number,
        "college_id": payload.college_id,
        "branch": payload.branch,
        "gpa": payload.gpa,
        "phone": payload.phone,
        "status": payload.status,
    }
    for k, v in mapping.items():
        if v is not None:
            fields.append(f"{k} = %s"); vals.append(v)
    if fields:
        vals.append(user_id)
        with get_db() as cur:
            cur.execute(f"UPDATE student_profiles SET {', '.join(fields)} WHERE user_id = %s", vals)
    with get_db() as cur:
        cur.execute(PROFILE_SELECT + " WHERE sp.user_id = %s", (user_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return _row_to_profile(row)
