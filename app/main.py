from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional

from .database import SessionLocal, engine
from .models import Base, Checkpoint, User
from . import schema
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Jyclo API")

# --- Security Config ---
import os
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-jyclo-dev-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_pin(plain_pin, hashed_pin):
    return pwd_context.verify(plain_pin, hashed_pin)

def get_pin_hash(pin):
    return pwd_context.hash(pin)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependencies ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
    
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

# ----------------- AUTH ENDPOINTS -----------------

@app.post("/api/auth/login", response_model=dict)
def login_or_register(auth_data: schema.UserAuth, db: Session = Depends(get_db)):
    """
    Unified Endpoint: Magic PIN.
    If email exists, checks PIN. If email doesn't exist, registers user.
    Returns: JWT Token.
    """
    if len(auth_data.pin) != 4 or not auth_data.pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN deve conter exatamente 4 dígitos numéricos.")

    user = db.query(User).filter(User.email == auth_data.email).first()
    
    if not user:
        # Register new user
        novo_user = User(email=auth_data.email, pin_hash=get_pin_hash(auth_data.pin))
        db.add(novo_user)
        db.commit()
        db.refresh(novo_user)
        user = novo_user
    else:
        # Verify existing user
        if not verify_pin(auth_data.pin, user.pin_hash):
            raise HTTPException(status_code=401, detail="PIN incorreto")

    # Issue token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# ----------------- API ENDPOINTS -----------------

@app.get("/api/cycles", response_model=dict)
def get_cycles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns all cycles and calculated statistics for the logged-in user.
    """
    now = datetime.utcnow()
    
    # All checkpoints ordered by start date descending
    checkpoints = db.query(Checkpoint).filter(Checkpoint.user_id == current_user.id).order_by(Checkpoint.data_inicio.desc()).all()
    
    # Calculate stats
    total = len(checkpoints)
    
    total_mes = sum(1 for c in checkpoints if c.data_inicio.month == now.month and c.data_inicio.year == now.year)
    total_ano = sum(1 for c in checkpoints if c.data_inicio.year == now.year)
    
    # Longest window
    longest_window = db.query(func.max(Checkpoint.duracao_horas)).filter(Checkpoint.user_id == current_user.id).scalar()
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
def create_cycle(cycle: schema.CheckpointCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Starts a new fasting cycle for the logged-in user.
    """
    novo = Checkpoint(
        user_id=current_user.id,
        data_inicio=cycle.data_inicio,
        comentario_inicio=cycle.comentario_inicio,
        status="ativo"
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@app.patch("/api/cycles/{checkpoint_id}/close", response_model=schema.CheckpointResponse)
def close_cycle(checkpoint_id: int, closing_data: schema.CheckpointClose, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Closes an active fasting cycle.
    """
    checkpoint = db.query(Checkpoint).filter(
        Checkpoint.id == checkpoint_id, 
        Checkpoint.user_id == current_user.id
    ).first()
    
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
def delete_cycle(checkpoint_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Deletes a cycle completely from the system.
    """
    checkpoint = db.query(Checkpoint).filter(
        Checkpoint.id == checkpoint_id,
        Checkpoint.user_id == current_user.id
    ).first()
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint não encontrado")
    
    db.delete(checkpoint)
    db.commit()
    return None