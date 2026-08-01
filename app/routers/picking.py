from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.allocation import generate_pick_tasks
from app.models.pick_tasks import PickTask
from app.auth.roles import require_roles

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/picking/generate")
def generate(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN"))
):

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


@router.get("/picking/tasks")
def get_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "PICKER"))
):

    tasks = (
        db.query(PickTask)
        .order_by(PickTask.sequence)
        .all()
    )

    return tasks
@router.get("/picking/task/{task_id}/serials")
def get_task_serials(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "PICKER"))
):
    serials = (
        db.query(PickSerial)
        .filter(PickSerial.task_id == task_id)
        .all()
    )

    return serials