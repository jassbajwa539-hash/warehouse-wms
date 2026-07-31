from sqlalchemy import Column, Integer, String
from app.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_no = Column(String, index=True)

    sku = Column(String, index=True)

    required_qty = Column(Integer)

    picked_qty = Column(Integer, default=0)