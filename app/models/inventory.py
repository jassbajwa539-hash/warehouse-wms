from sqlalchemy import Column, Integer, String
from app.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)

    sku = Column(String, nullable=False, index=True)

    serial_no = Column(String, unique=True, nullable=False, index=True)

    location = Column(String, nullable=False, index=True)

    box = Column(String, nullable=False)

    status = Column(String, default="AVAILABLE")

    picked_order = Column(String, nullable=True)