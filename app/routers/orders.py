from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import pandas as pd

from app.database import SessionLocal
from app.models.orders import Order
from app.models.order_items import OrderItem
from app.auth.roles import require_roles

router = APIRouter()


@router.post("/orders/upload")
async def upload_orders(
    file: UploadFile = File(...),
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        df = pd.read_excel(file.file)

        imported = 0

        for _, row in df.iterrows():

            order_no = str(row["Order No"]).strip()
            sku = str(row["SKU"]).strip()
            qty = int(row["Target"])

            order = (
                db.query(Order)
                .filter(Order.order_no == order_no)
                .first()
            )

            if not order:
                order = Order(
                    order_no=order_no,
                    status="PENDING"
                )
                db.add(order)

            db.add(
                OrderItem(
                    order_no=order_no,
                    sku=sku,
                    required_qty=qty,
                    picked_qty=0
                )
            )

            imported += 1

        db.commit()

        return {
            "success": True,
            "Imported": imported,
            "Uploaded By": current_user["username"]
        }

    except Exception as e:

        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "error": str(e)
            }
        )

    finally:
        db.close()