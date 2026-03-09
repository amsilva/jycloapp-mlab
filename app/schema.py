

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class CheckpointCreate(BaseModel):
    tipo: str
    data: date
    menu: str

class CheckpointBase(BaseModel):
    tipo: str
    data: date
    menu: Optional[str] = None

class CheckpointCreate(CheckpointBase):
    pass

class CheckpointResponse(CheckpointBase):
    id: int
    criado_em: datetime
    data_fim: Optional[datetime] = None
    duracao_horas: Optional[float] = None
    status: str
    
    class Config:
        orm_mode = True