from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
from auth import require_trainer, get_current_user
from schemas import NotificationCreate, NotificationOut

router = APIRouter()


# ── Create notification ────────────────────────────────────────────────────────
@router.post("", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationCreate, trainer: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute("""
            INSERT INTO notifications (title, message, target_type, target_id, created_by)
            VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at
        """, (payload.title, payload.message, payload.target_type,
              payload.target_id, trainer["id"]))
        row = cur.fetchone()
        nid, created_at = row[0], row[1]
    return {
        "id": nid, "title": payload.title, "message": payload.message,
        "target_type": payload.target_type, "target_id": payload.target_id,
        "created_by": trainer["id"], "created_by_name": trainer.get("full_name"),
        "created_at": str(created_at), "is_read": False
    }


# ── Get my notifications (student) ────────────────────────────────────────────
@router.get("/my", response_model=List[NotificationOut])
def get_my_notifications(current_user: dict = Depends(get_current_user)):
    sid = current_user["id"]
    with get_db() as cur:
        # get student's batch ids
        cur.execute("SELECT batch_id FROM batch_students WHERE student_id = %s", (sid,))
        batch_ids = [r[0] for r in cur.fetchall()]

        cur.execute("""
            SELECT n.id, n.title, n.message, n.target_type, n.target_id,
                   n.created_by, u.full_name, n.created_at,
                   (nr.student_id IS NOT NULL) AS is_read
            FROM notifications n
            LEFT JOIN pms_users u ON n.created_by = u.id
            LEFT JOIN notification_reads nr
                ON nr.notification_id = n.id AND nr.student_id = %s
            WHERE
                n.target_type = 'all'
                OR (n.target_type = 'student' AND n.target_id = %s)
                OR (n.target_type = 'batch' AND n.target_id = ANY(%s))
            ORDER BY n.created_at DESC
            LIMIT 50
        """, (sid, sid, batch_ids if batch_ids else [0]))
        rows = cur.fetchall()
    return [{
        "id": r[0], "title": r[1], "message": r[2], "target_type": r[3],
        "target_id": r[4], "created_by": r[5], "created_by_name": r[6],
        "created_at": str(r[7]), "is_read": bool(r[8])
    } for r in rows]


# ── Get all notifications (admin/trainer) ─────────────────────────────────────
@router.get("", response_model=List[NotificationOut])
def get_all_notifications(current_user: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute("""
            SELECT n.id, n.title, n.message, n.target_type, n.target_id,
                   n.created_by, u.full_name, n.created_at, FALSE
            FROM notifications n
            LEFT JOIN pms_users u ON n.created_by = u.id
            ORDER BY n.created_at DESC
            LIMIT 100
        """)
        rows = cur.fetchall()
    return [{
        "id": r[0], "title": r[1], "message": r[2], "target_type": r[3],
        "target_id": r[4], "created_by": r[5], "created_by_name": r[6],
        "created_at": str(r[7]), "is_read": False
    } for r in rows]


# ── Mark notification as read ──────────────────────────────────────────────────
@router.put("/{notification_id}/read")
def mark_read(notification_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute("""
            INSERT INTO notification_reads (notification_id, student_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING
        """, (notification_id, current_user["id"]))
    return {"message": "Marked as read"}


# ── Delete notification ────────────────────────────────────────────────────────
@router.delete("/{notification_id}")
def delete_notification(notification_id: int, trainer: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute("DELETE FROM notifications WHERE id = %s RETURNING id", (notification_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted"}
