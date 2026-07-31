from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.users import User
from app.auth.roles import require_roles
from app.auth.security import hash_password, verify_password

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# -------------------------
# Request Models
# -------------------------

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str


class UserUpdate(BaseModel):
    full_name: str
    role: str
    is_active: bool


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


class ResetPassword(BaseModel):
    new_password: str


# -------------------------
# Create User
# -------------------------

@router.post("/")
def create_user(
    data: UserCreate,
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        existing = (
            db.query(User)
            .filter(User.username == data.username)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

        user = User(
            username=data.username,
            password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role.upper(),
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "message": "User Created Successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active
            }
        }

    finally:
        db.close()


# -------------------------
# List Users
# -------------------------

@router.get("/")
def list_users(
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session =SessionLocal()

    try:

        users = db.query(User).all()

        return [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at
            }
            for u in users
        ]

    finally:
        db.close()


# -------------------------
# Get Single User
# -------------------------

@router.get("/{user_id}")
def get_user(
    user_id: int,
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at
        }

    finally:
        db.close()


# -------------------------
# Update User
# -------------------------

@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        user.full_name = data.full_name
        user.role = data.role.upper()
        user.is_active = data.is_active

        db.commit()

        return {
            "message": "User updated successfully"
        }

    finally:
        db.close()


# -------------------------
# Enable / Disable User
# -------------------------

@router.patch("/{user_id}/status")
def toggle_user_status(
    user_id: int,
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        user.is_active = not user.is_active

        db.commit()

        return {
            "message": "User status updated",
            "is_active": user.is_active
        }

    finally:
        db.close()


# -------------------------
# Change Own Password
# -------------------------

@router.post("/change-password")
def change_password(
    data: ChangePassword,
    current_user=Depends(require_roles("ADMIN", "PICKER"))
):

    db: Session = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.id == current_user["id"])
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        if not verify_password(
            data.old_password,
            user.password
        ):
            raise HTTPException(
                status_code=400,
                detail="Old password is incorrect"
            )

        user.password = hash_password(
            data.new_password
        )

        db.commit()

        return {
            "message": "Password changed successfully"
        }

    finally:
        db.close()


# -------------------------
# Reset User Password
# -------------------------

@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    data: ResetPassword,
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        user.password = hash_password(
            data.new_password
        )

        db.commit()

        return {
            "message": "Password reset successfully"
        }

    finally:
        db.close()