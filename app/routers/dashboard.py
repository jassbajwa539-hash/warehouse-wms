from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.auth.roles import require_roles

from app.models.inventory import Inventory
from app.models.orders import Order
from app.models.order_items import OrderItem
from app.models.pick_tasks import PickTask
from app.models.pick_serials import PickSerial

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/summary")
def dashboard_summary(
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        total_inventory = db.query(Inventory).count()

        total_orders = db.query(Order).count()

        pending_orders = db.query(Order).filter(
            Order.status == "PENDING"
        ).count()

        completed_orders = db.query(Order).filter(
            Order.status == "COMPLETED"
        ).count()

        total_tasks = db.query(PickTask).count()

        pending_tasks = db.query(PickTask).filter(
            PickTask.status == "PENDING"
        ).count()

        completed_tasks = db.query(PickTask).filter(
            PickTask.status == "COMPLETED"
        ).count()

        total_serials = db.query(PickSerial).count()

        picked_serials = db.query(PickSerial).filter(
            PickSerial.status == "PICKED"
        ).count()

        total_required = db.query(
            func.coalesce(func.sum(OrderItem.required_qty), 0)
        ).scalar()

        total_picked = db.query(
            func.coalesce(func.sum(OrderItem.picked_qty), 0)
        ).scalar()

        completion = 0

        if total_tasks > 0:
            completion = round(
                (completed_tasks / total_tasks) * 100,
                2
            )

        return {

            "inventory": {
                "total_inventory": total_inventory
            },

            "orders": {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "completed_orders": completed_orders
            },

            "picking": {
                "total_tasks": total_tasks,
                "pending_tasks": pending_tasks,
                "completed_tasks": completed_tasks,
                "completion_percentage": completion
            },

            "serials": {
                "total_serials": total_serials,
                "picked_serials": picked_serials
            },

            "quantity": {
                "required_qty": total_required,
                "picked_qty": total_picked
            }

        }

    finally:
        db.close()