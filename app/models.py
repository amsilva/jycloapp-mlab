from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    pin_hash = Column(String, nullable=False)
    
    checkpoints = relationship("Checkpoint", back_populates="user")

class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    data_inicio = Column(DateTime, nullable=False, default=datetime.utcnow) 
    comentario_inicio = Column(String, nullable=True)
    
    user = relationship("User", back_populates="checkpoints")
    
    # NOVOS CAMPOS
    data_fim = Column(DateTime, nullable=True)  # Quando encerrou
    comentario_fim = Column(String, nullable=True) # Como quebrou o jejum
    duracao_horas = Column(Float, nullable=True)  # Total de horas
    status = Column(String, default="ativo")  # "ativo" ou "encerrado"