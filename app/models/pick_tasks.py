from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class PickTask(Base):
    __tablename__ = "pick_tasks"

    id = Column(Integer, primary_key=True, index=True)

    order_no = Column(String, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"))

    sku = Column(String, index=True)

    location = Column(String, index=True)
    box = Column(String)

    required_qty = Column(Integer)
    picked_qty = Column(Integer, default=0)

    status = Column(String, default="PENDING")

    sequence = Column(Integer)