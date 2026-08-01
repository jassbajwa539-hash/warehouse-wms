from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.pick_tasks import PickTask
from app.models.pick_serials import PickSerial
from app.models.inventory import Inventory
from app.auth.dependencies import get_current_user

router = APIRouter(tags=["RF Picking"])


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
        return {
            "message": "No Pending Tasks"
        }

    return {
        "task_id": task.id,
        "order_no": task.order_no,
        "sku": task.sku,
        "location": task.location,
        "box": task.box,
        "required_qty": task.required_qty,
        "picked_qty": task.picked_qty,
        "status": task.status
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
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Validate Location
    if task.location.strip().upper() != data.location.strip().upper():
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid Location",
                "expected": task.location,
                "received": data.location
            }
        )

    # Validate Box
    if task.box.strip().upper() != data.box.strip().upper():
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid Box",
                "expected": task.box,
                "received": data.box
            }
        )

    # Find Serial
    serial = (
        db.query(PickSerial)
        .filter(
            PickSerial.task_id == task.id,
            PickSerial.serial_no == data.serial.strip()
        )
        .first()
    )

    if not serial:

        available_serials = (
            db.query(PickSerial.serial_no)
            .filter(PickSerial.task_id == task.id)
            .all()
        )

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Serial not found",
                "entered_serial": data.serial,
                "task_id": task.id,
                "available_serials": [x[0] for x in available_serials]
            }
        )

    if serial.status == "PICKED":
        raise HTTPException(
            status_code=400,
            detail="Serial already picked"
        )

    # Mark serial picked
    serial.status = "PICKED"

    # Update Inventory
    inventory = (
        db.query(Inventory)
        .filter(
            Inventory.serial_no == serial.serial_no
        )
        .first()
    )

    if inventory:
        inventory.status = "PICKED"

    # Update Task
    task.picked_qty += 1

    if task.picked_qty >= task.required_qty:
        task.status = "COMPLETED"

    db.commit()

    return {
        "success": True,
        "message": "Serial Picked Successfully",
        "task_id": task.id,
        "picked_qty": task.picked_qty,
        "required_qty": task.required_qty,
        "task_status": task.status
    }


@router.get("/rf/task/{task_id}/serials")
def task_serials(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    serials = (
        db.query(PickSerial)
        .filter(PickSerial.task_id == task_id)
        .all()
    )

    return serials