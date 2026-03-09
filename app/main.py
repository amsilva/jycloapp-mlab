from fastapi import FastAPI, HTTPException, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date
from .database import SessionLocal, engine
from .models import Base, Checkpoint
from fastapi.templating import Jinja2Templates
import datetime

app = FastAPI()

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
def index(request: Request, db: Session = Depends(get_db)):
    hoje = date.today()

    # Todas os checkpoints
    checkpoints = db.query(Checkpoint).order_by(Checkpoint.data_inicio.desc()).all()
    total = len(checkpoints)

    # Checkpoints do mês atual
    total_mes = db.query(Checkpoint).filter(
        extract("month", Checkpoint.data_inicio) == hoje.month,
        extract("year", Checkpoint.data_inicio) == hoje.year
    ).count()

    # Checkpoint do ano atual
    total_ano = db.query(Checkpoint).filter(
        extract("year", Checkpoint.data_inicio) == hoje.year
    ).count()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "checkpoints": checkpoints,
        "total_checkpoints": total,
        "total_mes": total_mes,
        "total_ano": total_ano
    })

@app.post("/novo-checkpoint")
def novo_checkpoint(
    tipo: str = Form(...),
    data_inicio: date = Form(...),
    menu: str = Form(...),
    db: Session = Depends(get_db)
):
    novo = Checkpoint(tipo=tipo, data_inicio=data_inicio, menu=menu)
    db.add(novo)
    db.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/encerrar-checkpoint/{checkpoint_id}")
async def encerrar_checkpoint(checkpoint_id: int):
    db = SessionLocal()
    try:
        # Buscar o checkpoint
        checkpoint = db.query(Checkpoint).filter(
            Checkpoint.id == checkpoint_id
        ).first()
        
        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint não encontrado")
        
        # Se já estiver encerrado, não permitir novo encerramento
        if checkpoint.status == "encerrado":
            raise HTTPException(status_code=400, detail="Checkpoint já está encerrado")
        
        # Definir data de fim
        agora = datetime.now()
        checkpoint.data_fim = agora
        
        # Calcular duração em horas
        data_inicio = datetime.combine(checkpoint.data_inicio, datetime.min.time())
        delta = agora - data_inicio
        checkpoint.duracao_horas = round(delta.total_seconds() / 3600, 2)
        
        # Atualizar status
        checkpoint.status = "encerrado"
        
        # Salvar
        db.commit()
        db.refresh(checkpoint)
        
        return {
            "success": True,
            "message": "Ciclo encerrado com sucesso",
            "duracao_horas": checkpoint.duracao_horas
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()



if __name__ == "__main__":
    print("Jycloapp starting...")