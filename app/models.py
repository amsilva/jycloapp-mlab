from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime
from .database import Base

class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    data_inicio = Column(DateTime, nullable=False, default=datetime.utcnow) 
    comentario_inicio = Column(String, nullable=True)
    
    # NOVOS CAMPOS
    data_fim = Column(DateTime, nullable=True)  # Quando encerrou
    comentario_fim = Column(String, nullable=True) # Como quebrou o jejum
    duracao_horas = Column(Float, nullable=True)  # Total de horas
    status = Column(String, default="ativo")  # "ativo" ou "encerrado"