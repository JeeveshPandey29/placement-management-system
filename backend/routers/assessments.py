from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
from auth import require_trainer, require_student, get_current_user
from schemas import AssessmentCreate, AssessmentOut, ScoreCreate, ScoreOut

router = APIRouter()

@router.post("", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
def create_assessment(payload: AssessmentCreate, trainer_user: dict = Depends(require_trainer)):
    try:
        with get_db() as cur:
            cur.execute(
                """INSERT INTO assessments (title, description, max_score, date)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (payload.title, payload.description, payload.max_score, payload.date)
            )
            assessment_id = cur.fetchone()[0]
        return {
            "id": assessment_id,
            "title": payload.title,
            "description": payload.description,
            "max_score": payload.max_score,
            "date": payload.date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[AssessmentOut])
def list_assessments(current_user: dict = Depends(get_current_user)):
    try:
        with get_db() as cur:
            cur.execute("SELECT id, title, description, max_score, date FROM assessments ORDER BY date DESC")
            rows = cur.fetchall()
            return [
                {"id": r[0], "title": r[1], "description": r[2], "max_score": r[3], "date": r[4]}
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my/scores", response_model=List[ScoreOut])
def get_my_assessment_scores(current_user: dict = Depends(require_student)):
    try:
        student_id = current_user["id"]
        with get_db() as cur:
            cur.execute(
                """SELECT s.id, s.assessment_id, s.student_id, u.email, s.score, s.feedback
                   FROM assessment_scores s
                   JOIN users u ON s.student_id = u.id
                   WHERE s.student_id = %s
                   ORDER BY s.id DESC""",
                (student_id,)
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "assessment_id": r[1],
                    "student_id": r[2],
                    "student_email": r[3],
                    "score": r[4],
                    "feedback": r[5]
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{assessment_id}/scores", response_model=ScoreOut, status_code=status.HTTP_201_CREATED)
def enter_assessment_score(assessment_id: int, payload: ScoreCreate, trainer_user: dict = Depends(require_trainer)):
    try:
        with get_db() as cur:
            # Verify student exists
            cur.execute("SELECT role FROM users WHERE id = %s", (payload.student_id,))
            row = cur.fetchone()
            if not row or row[0] != "student":
                raise HTTPException(status_code=400, detail="Invalid student ID")
            
            # Verify assessment exists
            cur.execute("SELECT max_score FROM assessments WHERE id = %s", (assessment_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Assessment not found")
            max_score = row[0]
            if payload.score > max_score:
                raise HTTPException(status_code=400, detail=f"Score cannot exceed maximum score of {max_score}")

            # Insert/Update score
            cur.execute(
                """INSERT INTO assessment_scores (assessment_id, student_id, score, feedback)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (assessment_id, student_id)
                   DO UPDATE SET score = EXCLUDED.score, feedback = EXCLUDED.feedback
                   RETURNING id""",
                (assessment_id, payload.student_id, payload.score, payload.feedback)
            )
            score_id = cur.fetchone()[0]
            
            cur.execute("SELECT email FROM users WHERE id = %s", (payload.student_id,))
            student_email = cur.fetchone()[0]
            
        return {
            "id": score_id,
            "assessment_id": assessment_id,
            "student_id": payload.student_id,
            "student_email": student_email,
            "score": payload.score,
            "feedback": payload.feedback
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{assessment_id}/scores", response_model=List[ScoreOut])
def get_assessment_scores(assessment_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_db() as cur:
            # If user is student, only show their own score. Otherwise show all.
            if current_user["role"] == "student":
                cur.execute(
                    """SELECT s.id, s.assessment_id, s.student_id, u.email, s.score, s.feedback
                       FROM assessment_scores s
                       JOIN users u ON s.student_id = u.id
                       WHERE s.assessment_id = %s AND s.student_id = %s""",
                    (assessment_id, current_user["id"])
                )
            else:
                cur.execute(
                    """SELECT s.id, s.assessment_id, s.student_id, u.email, s.score, s.feedback
                       FROM assessment_scores s
                       JOIN users u ON s.student_id = u.id
                       WHERE s.assessment_id = %s
                       ORDER BY s.score DESC""",
                    (assessment_id,)
                )
                
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "assessment_id": r[1],
                    "student_id": r[2],
                    "student_email": r[3],
                    "score": r[4],
                    "feedback": r[5]
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

