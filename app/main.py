from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date
from .database import SessionLocal, engine
from .models import Base, Checkpoint
from fastapi.templating import Jinja2Templates
from datetime import date


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
    checkpoints = db.query(Checkpoint).order_by(Checkpoint.data.desc()).all()
    total = len(checkpoints)

    # Checkpoints do mês atual
    total_mes = db.query(Checkpoint).filter(
        extract("month", Checkpoint.data) == hoje.month,
        extract("year", Checkpoint.data) == hoje.year
    ).count()

    # Checkpoint do ano atual
    total_ano = db.query(Checkpoint).filter(
        extract("year", Checkpoint.data) == hoje.year
    ).count()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "doacoes": checkpoints,
        "total_checkpoints": total,
        "total_mes": total_mes,
        "total_ano": total_ano
    })

@app.post("/novo-checkpoint")
def novo_checkpoint(
    tipo: str = Form(...),
    data: date = Form(...),
    menu: str = Form(...),
    db: Session = Depends(get_db)
):
    nova = Checkpoint(tipo=tipo, data=data, menu=menu)
    db.add(nova)
    db.commit()
    return RedirectResponse("/", status_code=303)


if __name__ == "__main__":
    print("Jycloapp starting...")