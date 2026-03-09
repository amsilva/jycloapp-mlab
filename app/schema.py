from pydantic import BaseModel
from datetime import date

class DoacaoCreate(BaseModel):
    tipo: str
    data: date
    local: str
