from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_db
from auth import require_admin, require_trainer, get_current_user
from schemas import BatchCreate, BatchUpdate, BatchOut, BatchStudentIn

router = APIRouter()


def _batch_row_to_dict(r) -> dict:
    return {
        "id": r[0], "name": r[1], "branch": r[2],
        "trainer_id": r[3], "trainer_name": r[4], "student_count": r[5]
    }


# ── List batches ───────────────────────────────────────────────────────────────
@router.get("", response_model=List[BatchOut])
def list_batches(current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        if current_user["role"] == "trainer":
            cur.execute("""
                SELECT b.id, b.name, b.branch, b.trainer_id, u.full_name,
                       COUNT(bs.student_id) AS student_count
                FROM batches b
                LEFT JOIN pms_users u ON b.trainer_id = u.id
                LEFT JOIN batch_students bs ON b.id = bs.batch_id
                WHERE b.trainer_id = %s
                GROUP BY b.id, u.full_name
                ORDER BY b.name
            """, (current_user["id"],))
        elif current_user["role"] == "student":
            cur.execute("""
                SELECT b.id, b.name, b.branch, b.trainer_id, u.full_name,
                       COUNT(bs2.student_id) AS student_count
                FROM batches b
                LEFT JOIN pms_users u ON b.trainer_id = u.id
                LEFT JOIN batch_students bs ON b.id = bs.batch_id
                LEFT JOIN batch_students bs2 ON b.id = bs2.batch_id
                WHERE bs.student_id = %s
                GROUP BY b.id, u.full_name
                ORDER BY b.name
            """, (current_user["id"],))
        else:
            cur.execute("""
                SELECT b.id, b.name, b.branch, b.trainer_id, u.full_name,
                       COUNT(bs.student_id) AS student_count
                FROM batches b
                LEFT JOIN pms_users u ON b.trainer_id = u.id
                LEFT JOIN batch_students bs ON b.id = bs.batch_id
                GROUP BY b.id, u.full_name
                ORDER BY b.name
            """)
        return [_batch_row_to_dict(r) for r in cur.fetchall()]


# ── Create batch ───────────────────────────────────────────────────────────────
@router.post("", response_model=BatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(payload: BatchCreate, admin: dict = Depends(require_admin)):
    with get_db() as cur:
        cur.execute(
            "INSERT INTO batches (name, branch, trainer_id) VALUES (%s, %s, %s) RETURNING id",
            (payload.name, payload.branch, payload.trainer_id)
        )
        bid = cur.fetchone()[0]
        trainer_name = None
        if payload.trainer_id:
            cur.execute("SELECT full_name FROM pms_users WHERE id = %s", (payload.trainer_id,))
            row = cur.fetchone()
            if row:
                trainer_name = row[0]
    return {"id": bid, "name": payload.name, "branch": payload.branch,
            "trainer_id": payload.trainer_id, "trainer_name": trainer_name, "student_count": 0}


# ── Update batch ───────────────────────────────────────────────────────────────
@router.put("/{batch_id}", response_model=BatchOut)
def update_batch(batch_id: int, payload: BatchUpdate, admin: dict = Depends(require_admin)):
    with get_db() as cur:
        fields, vals = [], []
        if payload.name is not None:
            fields.append("name = %s"); vals.append(payload.name)
        if payload.branch is not None:
            fields.append("branch = %s"); vals.append(payload.branch)
        if payload.trainer_id is not None:
            fields.append("trainer_id = %s"); vals.append(payload.trainer_id)
        if not fields:
            raise HTTPException(status_code=400, detail="Nothing to update")
        vals.append(batch_id)
        cur.execute(f"UPDATE batches SET {', '.join(fields)} WHERE id = %s", vals)
        cur.execute("""
            SELECT b.id, b.name, b.branch, b.trainer_id, u.full_name,
                   COUNT(bs.student_id)
            FROM batches b
            LEFT JOIN pms_users u ON b.trainer_id = u.id
            LEFT JOIN batch_students bs ON b.id = bs.batch_id
            WHERE b.id = %s
            GROUP BY b.id, u.full_name
        """, (batch_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _batch_row_to_dict(row)


# ── Delete batch ───────────────────────────────────────────────────────────────
@router.delete("/{batch_id}")
def delete_batch(batch_id: int, admin: dict = Depends(require_admin)):
    with get_db() as cur:
        cur.execute("DELETE FROM batches WHERE id = %s RETURNING id", (batch_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Batch not found")
    return {"message": "Batch deleted"}


# ── Get batch students ─────────────────────────────────────────────────────────
@router.get("/{batch_id}/students")
def get_batch_students(batch_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute("""
            SELECT u.id, u.email, u.full_name, sp.enrollment_number, sp.branch,
                   sp.gpa, sp.status
            FROM batch_students bs
            JOIN pms_users u ON bs.student_id = u.id
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE bs.batch_id = %s
            ORDER BY u.full_name
        """, (batch_id,))
        rows = cur.fetchall()
    return [{"id": r[0], "email": r[1], "full_name": r[2], "enrollment_number": r[3],
             "branch": r[4], "gpa": str(r[5]) if r[5] else None, "status": r[6]} for r in rows]


# ── Add students to batch ──────────────────────────────────────────────────────
@router.post("/{batch_id}/students")
def add_students_to_batch(batch_id: int, payload: BatchStudentIn,
                           admin: dict = Depends(require_admin)):
    with get_db() as cur:
        cur.execute("SELECT id, name FROM batches WHERE id = %s", (batch_id,))
        batch = cur.fetchone()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        batch_name = batch[1]
        added = 0
        for sid in payload.student_ids:
            try:
                cur.execute(
                    "INSERT INTO batch_students (batch_id, student_id) VALUES (%s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (batch_id, sid)
                )
                if cur.rowcount > 0:
                    added += 1
                    # Auto-notify each student
                    cur.execute(
                        "INSERT INTO notifications (title, message, target_type, target_id, created_by) "
                        "VALUES (%s, %s, 'student', %s, %s)",
                        (f"You've been added to Batch {batch_name}",
                         f"You have been assigned to training batch '{batch_name}'. Check your classes and schedule.",
                         sid, admin["id"])
                    )
            except Exception:
                pass
    return {"message": f"{added} student(s) added to batch"}


# ── Remove student from batch ──────────────────────────────────────────────────
@router.delete("/{batch_id}/students/{student_id}")
def remove_student_from_batch(batch_id: int, student_id: int,
                               admin: dict = Depends(require_admin)):
    with get_db() as cur:
        cur.execute(
            "DELETE FROM batch_students WHERE batch_id = %s AND student_id = %s RETURNING batch_id",
            (batch_id, student_id)
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Student not in this batch")
    return {"message": "Student removed from batch"}
