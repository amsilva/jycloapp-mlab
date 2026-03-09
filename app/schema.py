from pydantic import BaseModel
from datetime import date

class CheckpointCreate(BaseModel):
    tipo: str
    data: date
    menu: str
