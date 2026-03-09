from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date
from .database import SessionLocal, engine
from .models import Base, Doacao
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


"""trocando a rota / 
para que ela monte dados para os 3 contadores (tot, mes e ano)

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    doacoes = db.query(Doacao).order_by(Doacao.data.desc()).all()
    total = len(doacoes)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "doacoes": doacoes,
        "total_doacoes": total
    })
"""

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    hoje = date.today()

    # Todas as doações
    doacoes = db.query(Doacao).order_by(Doacao.data.desc()).all()
    total = len(doacoes)

    # Doações do mês atual
    total_mes = db.query(Doacao).filter(
        extract("month", Doacao.data) == hoje.month,
        extract("year", Doacao.data) == hoje.year
    ).count()

    # Doações do ano atual
    total_ano = db.query(Doacao).filter(
        extract("year", Doacao.data) == hoje.year
    ).count()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "doacoes": doacoes,
        "total_doacoes": total,
        "total_mes": total_mes,
        "total_ano": total_ano
    })

@app.post("/nova-doacao")
def nova_doacao(
    tipo: str = Form(...),
    data: date = Form(...),
    local: str = Form(...),
    db: Session = Depends(get_db)
):
    nova = Doacao(tipo=tipo, data=data, local=local)
    db.add(nova)
    db.commit()
    return RedirectResponse("/", status_code=303)
