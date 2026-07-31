from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
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

        # Read CSV
        df = pd.read_csv(file.file)

        # Remove blank rows
        df = df.fillna("")

        # Detect location column
        if "Location" in df.columns:
            location_column = "Location"
        elif "Sub Location" in df.columns:
            location_column = "Sub Location"
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Location column not found. Expected 'Location' or 'Sub Location'."
                }
            )

        required = ["SKU", "Serial Code", "Box"]

        for col in required:
            if col not in df.columns:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": f"Missing Column : {col}"
                    }
                )

        # Load all existing serials once
        existing_serials = {
            x[0]
            for x in db.query(Inventory.serial_no).all()
        }

        new_items = []

        imported = 0
        skipped = 0

        for _, row in df.iterrows():

            serial = str(row["Serial Code"]).strip()

            if serial == "":
                skipped += 1
                continue

            if serial in existing_serials:
                skipped += 1
                continue

            existing_serials.add(serial)

            new_items.append(
                Inventory(
                    sku=str(row["SKU"]).strip(),
                    serial_no=serial,
                    location=str(row[location_column]).strip(),
                    box=str(row["Box"]).strip(),
                    status="AVAILABLE"
                )
            )

            imported += 1

        # Bulk Insert
        if new_items:
            db.bulk_save_objects(new_items)
            db.commit()

        return {
            "success": True,
            "Imported": imported,
            "Skipped": skipped,
            "Total Rows": len(df),
            "Uploaded By": current_user["username"]
        }

    except Exception as e:

        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

    finally:
        db.close()