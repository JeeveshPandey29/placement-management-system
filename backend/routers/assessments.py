from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
from auth import require_trainer, require_student, get_current_user
from schemas import AssessmentCreate, AssessmentUpdate, AssessmentOut, ScoreCreate, ScoreOut

router = APIRouter()


@router.post("", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
def create_assessment(payload: AssessmentCreate, trainer: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute(
            "INSERT INTO assessments (title, description, max_score, date, batch_id) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (payload.title, payload.description, payload.max_score, payload.date, payload.batch_id)
        )
        aid = cur.fetchone()[0]
        batch_name = None
        if payload.batch_id:
            cur.execute("SELECT name FROM batches WHERE id = %s", (payload.batch_id,))
            row = cur.fetchone()
            batch_name = row[0] if row else None
    return {"id": aid, "title": payload.title, "description": payload.description,
            "max_score": payload.max_score, "date": payload.date,
            "batch_id": payload.batch_id, "batch_name": batch_name}


@router.get("", response_model=List[AssessmentOut])
def list_assessments(current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute("""
            SELECT a.id, a.title, a.description, a.max_score, a.date, a.batch_id, b.name
            FROM assessments a
            LEFT JOIN batches b ON a.batch_id = b.id
            ORDER BY a.date DESC
        """)
        rows = cur.fetchall()
    return [{"id": r[0], "title": r[1], "description": r[2], "max_score": r[3],
             "date": r[4], "batch_id": r[5], "batch_name": r[6]} for r in rows]


@router.get("/my/scores", response_model=List[ScoreOut])
def get_my_scores(student: dict = Depends(require_student)):
    with get_db() as cur:
        cur.execute("""
            SELECT s.id, s.assessment_id, s.student_id, u.email, u.full_name, s.score, s.feedback
            FROM assessment_scores s
            JOIN pms_users u ON s.student_id = u.id
            WHERE s.student_id = %s ORDER BY s.id DESC
        """, (student["id"],))
        rows = cur.fetchall()
    return [{"id": r[0], "assessment_id": r[1], "student_id": r[2],
             "student_email": r[3], "student_name": r[4], "score": r[5], "feedback": r[6]}
            for r in rows]


@router.post("/{assessment_id}/scores", response_model=ScoreOut, status_code=status.HTTP_201_CREATED)
def enter_score(assessment_id: int, payload: ScoreCreate, trainer: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute("SELECT role FROM pms_users WHERE id = %s", (payload.student_id,))
        row = cur.fetchone()
        if not row or row[0] != "student":
            raise HTTPException(status_code=400, detail="Invalid student ID")
        cur.execute("SELECT max_score FROM assessments WHERE id = %s", (assessment_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assessment not found")
        if payload.score > row[0]:
            raise HTTPException(status_code=400, detail=f"Score exceeds max ({row[0]})")
        cur.execute("""
            INSERT INTO assessment_scores (assessment_id, student_id, score, feedback)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (assessment_id, student_id)
            DO UPDATE SET score = EXCLUDED.score, feedback = EXCLUDED.feedback
            RETURNING id
        """, (assessment_id, payload.student_id, payload.score, payload.feedback))
        sid = cur.fetchone()[0]
        cur.execute("SELECT email, full_name FROM pms_users WHERE id = %s", (payload.student_id,))
        urow = cur.fetchone()
    return {"id": sid, "assessment_id": assessment_id, "student_id": payload.student_id,
            "student_email": urow[0], "student_name": urow[1],
            "score": payload.score, "feedback": payload.feedback}


@router.get("/{assessment_id}/scores", response_model=List[ScoreOut])
def get_scores(assessment_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        if current_user["role"] == "student":
            cur.execute("""
                SELECT s.id, s.assessment_id, s.student_id, u.email, u.full_name, s.score, s.feedback
                FROM assessment_scores s JOIN pms_users u ON s.student_id = u.id
                WHERE s.assessment_id = %s AND s.student_id = %s
            """, (assessment_id, current_user["id"]))
        else:
            cur.execute("""
                SELECT s.id, s.assessment_id, s.student_id, u.email, u.full_name, s.score, s.feedback
                FROM assessment_scores s JOIN pms_users u ON s.student_id = u.id
                WHERE s.assessment_id = %s ORDER BY s.score DESC
            """, (assessment_id,))
        rows = cur.fetchall()
    return [{"id": r[0], "assessment_id": r[1], "student_id": r[2],
             "student_email": r[3], "student_name": r[4], "score": r[5], "feedback": r[6]}
            for r in rows]


@router.put("/{assessment_id}", response_model=AssessmentOut)
def update_assessment(assessment_id: int, payload: AssessmentUpdate, trainer: dict = Depends(require_trainer)):
    fields, vals = [], []
    for k, v in payload.model_dump(exclude_none=True).items():
        fields.append(f"{k} = %s"); vals.append(v)
    if not fields:
        raise HTTPException(status_code=400, detail="Nothing to update")
    vals.append(assessment_id)
    with get_db() as cur:
        cur.execute(f"UPDATE assessments SET {', '.join(fields)} WHERE id = %s", vals)
        cur.execute("""
            SELECT a.id, a.title, a.description, a.max_score, a.date, a.batch_id, b.name
            FROM assessments a LEFT JOIN batches b ON a.batch_id = b.id
            WHERE a.id = %s
        """, (assessment_id,))
        r = cur.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"id": r[0], "title": r[1], "description": r[2], "max_score": r[3],
            "date": r[4], "batch_id": r[5], "batch_name": r[6]}


@router.delete("/{assessment_id}")
def delete_assessment(assessment_id: int, trainer: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute("DELETE FROM assessments WHERE id = %s RETURNING id", (assessment_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Assessment not found")
    return {"message": "Assessment deleted"}
