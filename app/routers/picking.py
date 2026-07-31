from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.allocation import generate_pick_tasks
from app.models.pick_tasks import PickTask
from app.auth.roles import require_roles

router = APIRouter()


@router.post("/picking/generate")
def generate(
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        # Prevent duplicate generation
        existing = db.query(PickTask).count()

        if existing > 0:
            return {
                "message": "Pick tasks already exist.",
                "tasks_created": existing,
                "generated_by": current_user["username"]
            }

        generate_pick_tasks(db)

        total = db.query(PickTask).count()

        return {
            "message": "Pick List Generated Successfully",
            "tasks_created": total,
            "generated_by": current_user["username"]
        }

    finally:
        db.close()