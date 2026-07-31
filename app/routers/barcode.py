from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.pick_tasks import PickTask
from app.models.pick_serials import PickSerial
from app.auth.roles import require_roles
from app.services.order_completion import update_order_status

router = APIRouter()


class BarcodeScan(BaseModel):
    task_id: int
    barcode: str


@router.post("/rf/scan/barcode")
def scan_barcode(
    data: BarcodeScan,
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

        if task.status == "COMPLETED":
            return {
                "success": False,
                "message": "Task Already Completed"
            }

        serial = (
            db.query(PickSerial)
            .filter(
                PickSerial.task_id == data.task_id,
                PickSerial.serial_no == data.barcode
            )
            .first()
        )

        if serial is None:
            return {
                "success": False,
                "message": "Wrong Barcode"
            }

        if serial.status == "PICKED":
            return {
                "success": False,
                "message": "Barcode Already Picked"
            }

        # Mark serial as picked
        serial.status = "PICKED"

        # Increase picked quantity
        task.picked_qty += 1

        # Complete task if required quantity reached
        if task.picked_qty >= task.required_qty:
            task.status = "COMPLETED"

        # Save changes
        db.commit()

        # Automatically update parent order status
        update_order_status(
            db=db,
            order_no=task.order_no
        )

        # Fetch next pending task
        next_task = (
            db.query(PickTask)
            .filter(PickTask.status == "PENDING")
            .order_by(PickTask.sequence)
            .first()
        )

        response = {
            "success": True,
            "message": (
                "Task Completed"
                if task.status == "COMPLETED"
                else "Barcode Scanned"
            ),
            "completed_task": task.id,
            "order_no": task.order_no,
            "picked_qty": task.picked_qty,
            "required_qty": task.required_qty,
            "picked_by": current_user["username"]
        }

        if next_task:
            response["next_task"] = {
                "task_id": next_task.id,
                "order_no": next_task.order_no,
                "sku": next_task.sku,
                "location": next_task.location,
                "box": next_task.box,
                "required_qty": next_task.required_qty,
                "picked_qty": next_task.picked_qty
            }
        else:
            response["message"] = "All Picking Completed"

        return response

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()