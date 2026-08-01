from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.pick_tasks import PickTask
from app.models.pick_serials import PickSerial
from app.models.inventory import Inventory
from app.auth.dependencies import get_current_user

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ScanRequest(BaseModel):
    task_id: int
    location: str
    box: str
    serial: str


@router.get("/rf/next")
def next_pick(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    task = (
        db.query(PickTask)
        .filter(PickTask.status == "PENDING")
        .order_by(PickTask.sequence)
        .first()
    )

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


@router.post("/rf/scan")
def scan(
    data: ScanRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    task = (
        db.query(PickTask)
        .filter(PickTask.id == data.task_id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.location != data.location:
        raise HTTPException(status_code=400, detail="Invalid Location")

    if task.box != data.box:
        raise HTTPException(status_code=400, detail="Invalid Box")

    serial = (
        db.query(PickSerial)
        .filter(
            PickSerial.task_id == task.id,
            PickSerial.serial_no == data.serial,
            PickSerial.status == "PENDING"
        )
        .first()
    )

    if not serial:
        raise HTTPException(
            status_code=400,
            detail="Invalid or Already Picked Serial"
        )

    serial.status = "PICKED"

    inventory = (
        db.query(Inventory)
        .filter(Inventory.serial_no == data.serial)
        .first()
    )

    if inventory:
        inventory.status = "PICKED"

    task.picked_qty += 1

    if task.picked_qty >= task.required_qty:
        task.status = "COMPLETED"

    db.commit()

    return {
        "success": True,
        "message": "Serial Picked Successfully",
        "picked_qty": task.picked_qty,
        "required_qty": task.required_qty,
        "task_status": task.status
    }