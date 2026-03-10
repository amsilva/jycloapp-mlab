from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CheckpointBase(BaseModel):
    data_inicio: datetime
    comentario_inicio: Optional[str] = None

class CheckpointCreate(CheckpointBase):
    pass

class CheckpointClose(BaseModel):
    comentario_fim: Optional[str] = None
    data_fim: Optional[datetime] = None

class CheckpointResponse(CheckpointBase):
    id: int
    data_fim: Optional[datetime] = None
    comentario_fim: Optional[str] = None
    duracao_horas: Optional[float] = None
    status: str
    
    class Config:
        from_attributes = True # updated from orm_mode=True for Pydantic v2 compatibility