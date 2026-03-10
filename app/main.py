from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from .database import SessionLocal, engine
from .models import Base, Checkpoint
from . import schema
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Jyclo API")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    Serves the main SPA HTML file.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# ----------------- API ENDPOINTS -----------------

@app.get("/api/cycles", response_model=dict)
def get_cycles(db: Session = Depends(get_db)):
    """
    Returns all cycles and calculated statistics.
    """
    now = datetime.utcnow()
    
    # All checkpoints ordered by start date descending
    checkpoints = db.query(Checkpoint).order_by(Checkpoint.data_inicio.desc()).all()
    
    # Calculate stats
    total = len(checkpoints)
    
    total_mes = sum(1 for c in checkpoints if c.data_inicio.month == now.month and c.data_inicio.year == now.year)
    total_ano = sum(1 for c in checkpoints if c.data_inicio.year == now.year)
    
    # Longest window
    longest_window = db.query(func.max(Checkpoint.duracao_horas)).scalar()
    longest_window = longest_window if longest_window else 0.0

    return {
        "checkpoints": [schema.CheckpointResponse.from_orm(c) for c in checkpoints],
        "stats": {
            "total": total,
            "total_mes": total_mes,
            "total_ano": total_ano,
            "longest_window": longest_window
        }
    }

@app.post("/api/cycles", response_model=schema.CheckpointResponse, status_code=status.HTTP_201_CREATED)
def create_cycle(cycle: schema.CheckpointCreate, db: Session = Depends(get_db)):
    """
    Starts a new fasting cycle.
    """
    novo = Checkpoint(
        data_inicio=cycle.data_inicio,
        comentario_inicio=cycle.comentario_inicio,
        status="ativo"
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@app.patch("/api/cycles/{checkpoint_id}/close", response_model=schema.CheckpointResponse)
def close_cycle(checkpoint_id: int, closing_data: schema.CheckpointClose, db: Session = Depends(get_db)):
    """
    Closes an active fasting cycle.
    """
    checkpoint = db.query(Checkpoint).filter(Checkpoint.id == checkpoint_id).first()
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint não encontrado")
    
    if checkpoint.status == "encerrado":
        raise HTTPException(status_code=400, detail="Checkpoint já está encerrado")
    
    agora = closing_data.data_fim if closing_data.data_fim else datetime.utcnow()
    # Ensure agora is offset-naive to compare with data_inicio
    if agora.tzinfo is not None:
        agora = agora.replace(tzinfo=None)
        
    # Check if end time is before start time
    if agora < checkpoint.data_inicio:
        raise HTTPException(status_code=400, detail="Data de encerramento não pode ser anterior à data de início")

    checkpoint.data_fim = agora
    checkpoint.comentario_fim = closing_data.comentario_fim
    
    # Calcular duração em horas
    delta = agora - checkpoint.data_inicio
    checkpoint.duracao_horas = round(delta.total_seconds() / 3600, 2)
    checkpoint.status = "encerrado"
    
    db.commit()
    db.refresh(checkpoint)
    
    return checkpoint

@app.delete("/api/cycles/{checkpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cycle(checkpoint_id: int, db: Session = Depends(get_db)):
    """
    Deletes a cycle completely from the system.
    """
    checkpoint = db.query(Checkpoint).filter(Checkpoint.id == checkpoint_id).first()
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint não encontrado")
    
    db.delete(checkpoint)
    db.commit()
    return None