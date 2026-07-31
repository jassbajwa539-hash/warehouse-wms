from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base


class PickSerial(Base):
    __tablename__ = "pick_serials"

    id = Column(Integer, primary_key=True, index=True)

    task_id = Column(Integer, ForeignKey("pick_tasks.id"))

    serial_no = Column(String, unique=True, index=True)

    status = Column(String, default="PENDING")