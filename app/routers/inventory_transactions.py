from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.auth.roles import require_roles

from app.models.inventory import Inventory
from app.models.inventory_transactions import InventoryTransaction

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory Transactions"]
)


class InventoryAdjustment(BaseModel):
    serial_no: str
    quantity: int
    remarks: str


@router.post("/adjust-in")
def adjust_in(
    data: InventoryAdjustment,
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        inventory = (
            db.query(Inventory)
            .filter(
                Inventory.serial_no == data.serial_no
            )
            .first()
        )

        if not inventory:
            raise HTTPException(
                404,
                "Inventory not found"
            )

        inventory.available_qty += data.quantity

        transaction = InventoryTransaction(
            sku=inventory.sku,
            serial_no=inventory.serial_no,
            transaction_type="ADJUST_IN",
            quantity=data.quantity,
            to_location=inventory.location,
            remarks=data.remarks,
            performed_by=current_user["username"]
        )

        db.add(transaction)

        db.commit()

        return {
            "message": "Inventory increased successfully"
        }

    finally:
        db.close()


@router.post("/adjust-out")
def adjust_out(
    data: InventoryAdjustment,
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        inventory = (
            db.query(Inventory)
            .filter(
                Inventory.serial_no == data.serial_no
            )
            .first()
        )

        if not inventory:
            raise HTTPException(
                404,
                "Inventory not found"
            )

        if inventory.available_qty < data.quantity:
            raise HTTPException(
                400,
                "Insufficient inventory"
            )

        inventory.available_qty -= data.quantity

        transaction = InventoryTransaction(
            sku=inventory.sku,
            serial_no=inventory.serial_no,
            transaction_type="ADJUST_OUT",
            quantity=data.quantity,
            from_location=inventory.location,
            remarks=data.remarks,
            performed_by=current_user["username"]
        )

        db.add(transaction)

        db.commit()

        return {
            "message": "Inventory decreased successfully"
        }

    finally:
        db.close()


@router.get("/transactions")
def transaction_history(
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        rows = (
            db.query(InventoryTransaction)
            .order_by(
                InventoryTransaction.created_at.desc()
            )
            .all()
        )

        return rows

    finally:
        db.close()