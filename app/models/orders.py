from sqlalchemy import Column, Integer, String
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    order_no = Column(String, index=True)

    status = Column(String, default="PENDING")