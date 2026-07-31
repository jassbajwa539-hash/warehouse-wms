from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.pick_tasks import PickTask
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/rf/next")
def next_pick(current_user=Depends(get_current_user)):

    db: Session = SessionLocal()

    task = (
        db.query(PickTask)
        .filter(PickTask.status == "PENDING")
        .order_by(PickTask.sequence)
        .first()
    )

    db.close()

    if not task:
        return {"message": "No Pending Tasks"}

    return {
        "task_id": task.id,
        "order_no": task.order_no,
        "sku": task.sku,
        "location": task.location,
        "box": task.box,
        "required_qty": task.required_qty,
        "picked_qty": task.picked_qty,
        "user": {
            "id": current_user["user_id"],
            "username": current_user["username"],
            "role": current_user["role"]
        }
    }