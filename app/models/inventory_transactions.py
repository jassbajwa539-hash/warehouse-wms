from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)

    sku = Column(String(100), nullable=False)

    serial_no = Column(String(150))

    transaction_type = Column(String(30), nullable=False)
    # ADJUST_IN
    # ADJUST_OUT
    # TRANSFER

    from_location = Column(String(100))
    to_location = Column(String(100))

    quantity = Column(Integer, default=1)

    remarks = Column(String(300))

    performed_by = Column(String(100))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )