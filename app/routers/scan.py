from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.pick_tasks import PickTask
from app.auth.roles import require_roles

router = APIRouter()


class LocationScan(BaseModel):
    task_id: int
    location: str


@router.post("/rf/scan/location")
def scan_location(
    data: LocationScan,
    current_user=Depends(require_roles("ADMIN", "PICKER"))
):

    db: Session = SessionLocal()

    try:

        task = (
            db.query(PickTask)
            .filter(PickTask.id == data.task_id)
            .first()
        )

        if task is None:
            return {
                "success": False,
                "message": "Task Not Found"
            }

        if task.status != "PENDING":
            return {
                "success": False,
                "message": "Task Already Completed"
            }

        if task.location.strip().upper() != data.location.strip().upper():
            return {
                "success": False,
                "message": "Wrong Location",
                "expected": task.location
            }

        return {
            "success": True,
            "message": "Location Verified",
            "task_id": task.id,
            "order_no": task.order_no,
            "sku": task.sku,
            "location": task.location,
            "box": task.box,
            "required_qty": task.required_qty,
            "picked_qty": task.picked_qty,
            "verified_by": current_user["username"]
        }

    finally:
        db.close()