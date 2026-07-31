from sqlalchemy.orm import Session

from app.models.orders import Order
from app.models.pick_tasks import PickTask


def update_order_status(db: Session, order_no: str):

    total = (
        db.query(PickTask)
        .filter(PickTask.order_no == order_no)
        .count()
    )

    completed = (
        db.query(PickTask)
        .filter(
            PickTask.order_no == order_no,
            PickTask.status == "COMPLETED"
        )
        .count()
    )

    order = (
        db.query(Order)
        .filter(Order.order_no == order_no)
        .first()
    )

    if order is None:
        return

    if total > 0 and total == completed:
        order.status = "COMPLETED"
    else:
        order.status = "PENDING"

    db.commit()