from sqlalchemy import Column, Integer, String, Date, DateTime
from datetime import datetime
from .database import Base

class Doacao(Base):
    __tablename__ = "doacoes"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)
    data = Column(Date, nullable=False)
    local = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
