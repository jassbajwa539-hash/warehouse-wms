from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.order_items import OrderItem
from app.models.pick_tasks import PickTask
from app.models.pick_serials import PickSerial


def generate_pick_tasks(db: Session):

    # Clear previous picking
    db.query(PickSerial).delete()
    db.query(PickTask).delete()

    db.commit()

    sequence = 1

    # Load all order items
    order_items = db.query(OrderItem).all()

    # Load all available inventory ONCE
    inventory = (
        db.query(Inventory)
        .filter(Inventory.status == "AVAILABLE")
        .order_by(
            Inventory.sku,
            Inventory.location,
            Inventory.box,
            Inventory.serial_no
        )
        .all()
    )

    # Group inventory by SKU
    inventory_by_sku = defaultdict(list)

    for inv in inventory:
        inventory_by_sku[inv.sku].append(inv)

    tasks = []

    serials = []

    reserved_inventory = []

    for item in order_items:

        available = inventory_by_sku[item.sku][:item.required_qty]

        if not available:
            continue

        grouped = defaultdict(list)

        for inv in available:
            grouped[(inv.location, inv.box)].append(inv)

        for (location, box), inv_list in grouped.items():

            task = PickTask(
                order_no=item.order_no,
                order_item_id=item.id,
                sku=item.sku,
                location=location,
                box=box,
                required_qty=len(inv_list),
                picked_qty=0,
                status="PENDING",
                sequence=sequence
            )

            tasks.append(task)

            sequence += 1

        # Remove allocated inventory
        inventory_by_sku[item.sku] = inventory_by_sku[item.sku][item.required_qty:]

    # Bulk insert tasks
    db.bulk_save_objects(tasks)

    db.commit()

    # Reload tasks to get IDs
    created_tasks = (
        db.query(PickTask)
        .order_by(PickTask.sequence)
        .all()
    )

    task_index = 0

    # Build serials
    inventory_by_sku = defaultdict(list)

    for inv in inventory:
        if inv.status == "AVAILABLE":
            inventory_by_sku[inv.sku].append(inv)

    for item in order_items:

        available = inventory_by_sku[item.sku][:item.required_qty]

        grouped = defaultdict(list)

        for inv in available:
            grouped[(inv.location, inv.box)].append(inv)

        for _, inv_list in grouped.items():

            task = created_tasks[task_index]

            for inv in inv_list:

                serials.append(
                    PickSerial(
                        task_id=task.id,
                        serial_no=inv.serial_no,
                        status="PENDING"
                    )
                )

                inv.status = "RESERVED"

                reserved_inventory.append(inv)

            task_index += 1

        inventory_by_sku[item.sku] = inventory_by_sku[item.sku][item.required_qty:]

    db.bulk_save_objects(serials)

    db.commit()