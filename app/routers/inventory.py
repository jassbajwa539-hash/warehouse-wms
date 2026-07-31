from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import pandas as pd

from app.database import SessionLocal
from app.models.inventory import Inventory
from app.auth.roles import require_roles

router = APIRouter()


@router.post("/inventory/upload")
async def upload_inventory(
    file: UploadFile = File(...),
    current_user=Depends(require_roles("ADMIN"))
):

    db: Session = SessionLocal()

    try:

        # If uploading Excel use read_excel instead
        # df = pd.read_excel(file.file)

        df = pd.read_csv(file.file)

        imported = 0
        skipped = 0

        for _, row in df.iterrows():

            serial = str(row["Serial Code"]).strip()

            existing = (
                db.query(Inventory)
                .filter(Inventory.serial_no == serial)
                .first()
            )

            if existing:
                skipped += 1
                continue

            item = Inventory(
                sku=str(row["SKU"]).strip(),
                serial_no=serial,
                location=str(row["Location"]).strip(),
                box=str(row["Box"]).strip(),
                status="AVAILABLE"
            )

            db.add(item)
            imported += 1

        db.commit()

        return {
            "Imported": imported,
            "Skipped": skipped,
            "UploadedBy": current_user["username"]
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