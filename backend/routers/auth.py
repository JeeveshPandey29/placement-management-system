import secrets
import csv
import io
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from database import get_db
from auth import hash_password, verify_password, create_token, get_current_user, require_admin
from schemas import (
    UserLogin, UserOut, SetPasswordIn, ChangePasswordIn,
    ForgotPasswordIn, ResetPasswordIn, AdminSetupIn, CreateUserIn
)

router = APIRouter()


# ── One-time admin bootstrap ───────────────────────────────────────────────────
@router.post("/setup/admin", response_model=UserOut, status_code=status.HTTP_201_CREATED,
             tags=["Setup"])
def setup_first_admin(payload: AdminSetupIn):
    """Works ONLY when zero admin accounts exist."""
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) FROM pms_users WHERE role = 'admin'")
        if cur.fetchone()[0] > 0:
            raise HTTPException(status_code=403,
                                detail="Admin already exists. Use admin panel to add more.")
        hashed = hash_password(payload.password)
        cur.execute(
            "INSERT INTO pms_users (email, password, role, full_name, must_change_password) "
            "VALUES (%s, %s, 'admin', %s, FALSE) RETURNING id",
            (payload.email, hashed, payload.full_name)
        )
        uid = cur.fetchone()[0]
    return {"id": uid, "email": payload.email, "role": "admin",
            "full_name": payload.full_name, "must_change_password": False}


# ── Login ──────────────────────────────────────────────────────────────────────
@router.post("/login", tags=["Authentication"])
def login(payload: UserLogin):
    with get_db() as cur:
        cur.execute(
            "SELECT id, password, role, full_name, must_change_password FROM pms_users WHERE email = %s",
            (payload.email,)
        )
        row = cur.fetchone()
    if not row or not verify_password(payload.password, row[1]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(row[0], row[2])
    token["must_change_password"] = row[4]
    token["full_name"] = row[3]
    return token


# ── Current user ───────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserOut, tags=["Authentication"])
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ── Set password (first-login flow) ───────────────────────────────────────────
@router.post("/set-password", tags=["Authentication"])
def set_password(payload: SetPasswordIn, current_user: dict = Depends(get_current_user)):
    hashed = hash_password(payload.new_password)
    with get_db() as cur:
        cur.execute(
            "UPDATE pms_users SET password = %s, must_change_password = FALSE WHERE id = %s",
            (hashed, current_user["id"])
        )
    return {"message": "Password updated successfully"}


# ── Change password ────────────────────────────────────────────────────────────
@router.post("/change-password", tags=["Authentication"])
def change_password(payload: ChangePasswordIn, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute("SELECT password FROM pms_users WHERE id = %s", (current_user["id"],))
        row = cur.fetchone()
    if not row or not verify_password(payload.old_password, row[0]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    hashed = hash_password(payload.new_password)
    with get_db() as cur:
        cur.execute(
            "UPDATE pms_users SET password = %s, must_change_password = FALSE WHERE id = %s",
            (hashed, current_user["id"])
        )
    return {"message": "Password changed successfully"}


# ── Forgot password ────────────────────────────────────────────────────────────
@router.post("/forgot-password", tags=["Authentication"])
def forgot_password(payload: ForgotPasswordIn):
    with get_db() as cur:
        cur.execute("SELECT id FROM pms_users WHERE email = %s", (payload.email,))
        row = cur.fetchone()
    if not row:
        return {"message": "If that email exists, a reset token has been generated."}
    user_id = row[0]
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=2)
    with get_db() as cur:
        cur.execute("UPDATE password_reset_tokens SET used = TRUE WHERE user_id = %s", (user_id,))
        cur.execute(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
            (user_id, token, expires)
        )
    return {"message": "Reset token generated.", "reset_token": token,
            "note": "In production this would be emailed."}


# ── Reset password ─────────────────────────────────────────────────────────────
@router.post("/reset-password", tags=["Authentication"])
def reset_password(payload: ResetPasswordIn):
    with get_db() as cur:
        cur.execute(
            "SELECT user_id, expires_at, used FROM password_reset_tokens WHERE token = %s",
            (payload.token,)
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user_id, expires_at, used = row
    if used:
        raise HTTPException(status_code=400, detail="Reset token already used")
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")
    hashed = hash_password(payload.new_password)
    with get_db() as cur:
        cur.execute(
            "UPDATE pms_users SET password = %s, must_change_password = FALSE WHERE id = %s",
            (hashed, user_id)
        )
        cur.execute("UPDATE password_reset_tokens SET used = TRUE WHERE token = %s", (payload.token,))
    return {"message": "Password reset successfully. Please log in."}


# ── Admin: Create single user ──────────────────────────────────────────────────
@router.post("/admin/users", response_model=UserOut, status_code=status.HTTP_201_CREATED,
             tags=["Admin"])
def admin_create_user(payload: CreateUserIn, admin: dict = Depends(require_admin)):
    """
    Default password = enrollment_number for students, email prefix for trainers/admins.
    must_change_password = TRUE so they set their own on first login.
    """
    if payload.role == "student" and payload.enrollment_number:
        default_pw = payload.enrollment_number  # enrollment no as default password
    else:
        default_pw = payload.email.split("@")[0]  # email prefix for trainers/admins

    hashed = hash_password(default_pw)
    with get_db() as cur:
        cur.execute("SELECT id FROM pms_users WHERE email = %s", (payload.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already in use")
        cur.execute(
            "INSERT INTO pms_users (email, password, role, full_name, must_change_password) "
            "VALUES (%s, %s, %s, %s, TRUE) RETURNING id",
            (payload.email, hashed, payload.role, payload.full_name)
        )
        uid = cur.fetchone()[0]
        if payload.role == "student":
            cur.execute(
                "INSERT INTO student_profiles "
                "(user_id, college_id, enrollment_number, branch, status) "
                "VALUES (%s, 1, %s, %s, 'unplaced')",
                (uid, payload.enrollment_number, payload.branch)
            )
    return {"id": uid, "email": payload.email, "role": payload.role,
            "full_name": payload.full_name, "must_change_password": True}


# ── Admin: Bulk upload via CSV ─────────────────────────────────────────────────
@router.post("/admin/users/bulk", tags=["Admin"])
async def admin_bulk_upload(
    file: UploadFile = File(...),
    admin: dict = Depends(require_admin)
):
    """
    CSV columns: full_name, email, role, enrollment_number (optional), branch (optional)
    Default password = enrollment_number for students, email prefix for others.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    created, skipped, errors = [], [], []

    with get_db() as cur:
        for i, row in enumerate(reader, start=2):  # row 2 = first data row
            try:
                full_name = row.get("full_name", "").strip()
                email = row.get("email", "").strip().lower()
                role = row.get("role", "student").strip().lower()
                enrollment_number = row.get("enrollment_number", "").strip() or None
                branch = row.get("branch", "").strip() or None

                if not full_name or not email:
                    errors.append(f"Row {i}: full_name and email are required")
                    continue
                if role not in ("admin", "trainer", "student"):
                    errors.append(f"Row {i}: invalid role '{role}'")
                    continue

                # Check duplicate
                cur.execute("SELECT id FROM pms_users WHERE email = %s", (email,))
                if cur.fetchone():
                    skipped.append(email)
                    continue

                default_pw = enrollment_number if (role == "student" and enrollment_number) \
                    else email.split("@")[0]
                hashed = hash_password(default_pw)

                cur.execute(
                    "INSERT INTO pms_users (email, password, role, full_name, must_change_password) "
                    "VALUES (%s, %s, %s, %s, TRUE) RETURNING id",
                    (email, hashed, role, full_name)
                )
                uid = cur.fetchone()[0]

                if role == "student":
                    cur.execute(
                        "INSERT INTO student_profiles "
                        "(user_id, college_id, enrollment_number, branch, status) "
                        "VALUES (%s, 1, %s, %s, 'unplaced')",
                        (uid, enrollment_number, branch)
                    )
                created.append({"email": email, "role": role, "default_password": default_pw})

            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")

    return {
        "created": len(created),
        "skipped_duplicates": len(skipped),
        "errors": errors,
        "users": created
    }


# ── Admin: List all users ──────────────────────────────────────────────────────
@router.get("/admin/users", tags=["Admin"])
def admin_list_users(role: str = None, admin: dict = Depends(require_admin)):
    with get_db() as cur:
        if role:
            cur.execute(
                "SELECT id, email, role, full_name, must_change_password, created_at "
                "FROM pms_users WHERE role = %s ORDER BY full_name", (role,)
            )
        else:
            cur.execute(
                "SELECT id, email, role, full_name, must_change_password, created_at "
                "FROM pms_users ORDER BY role, full_name"
            )
        rows = cur.fetchall()
    return [{"id": r[0], "email": r[1], "role": r[2], "full_name": r[3],
             "must_change_password": r[4], "created_at": str(r[5])} for r in rows]


# ── Admin: Delete user ─────────────────────────────────────────────────────────
@router.delete("/admin/users/{user_id}", tags=["Admin"])
def admin_delete_user(user_id: int, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    with get_db() as cur:
        cur.execute("DELETE FROM pms_users WHERE id = %s RETURNING id", (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}
