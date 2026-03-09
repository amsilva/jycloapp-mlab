from sqlalchemy import Column, Integer, String, Date, DateTime
from datetime import datetime
from .database import Base

class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)
    data = Column(Date, nullable=False)
    menu = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
