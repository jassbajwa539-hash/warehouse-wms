from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.order_items import OrderItem
from app.models.pick_tasks import PickTask
from app.models.pick_serials import PickSerial


def generate_pick_tasks(db: Session):

    db.query(PickSerial).delete()
    db.query(PickTask).delete()

    sequence = 1

    order_items = db.query(OrderItem).all()

    for item in order_items:

        inventory = (
            db.query(Inventory)
            .filter(
                Inventory.sku == item.sku,
                Inventory.status == "AVAILABLE"
            )
            .order_by(Inventory.location, Inventory.box, Inventory.serial_no)
            .limit(item.required_qty)
            .all()
        )

        grouped = defaultdict(list)

        for inv in inventory:
            grouped[(inv.location, inv.box)].append(inv)

        for (location, box), serials in grouped.items():

            task = PickTask(
                order_no=item.order_no,
                order_item_id=item.id,
                sku=item.sku,
                location=location,
                box=box,
                required_qty=len(serials),
                picked_qty=0,
                status="PENDING",
                sequence=sequence
            )

            db.add(task)
            db.flush()      # Get task.id

            for inv in serials:

                db.add(
                    PickSerial(
                        task_id=task.id,
                        serial_no=inv.serial_no,
                        status="PENDING"
                    )
                )

                inv.status = "RESERVED"

            sequence += 1

    db.commit()