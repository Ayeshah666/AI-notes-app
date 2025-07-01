from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, User, Note
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForCausalLM,
    TextGenerationPipeline,
)
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

# --- FastAPI Init ---
app = FastAPI()
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- JWT & Auth ---
SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid token scheme")
    payload = decode_token(token)
    return payload.get("sub")


# --- Pydantic Models ---
class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class NoteCreate(BaseModel):
    title: str
    content: str


class CorrectionRequest(BaseModel):
    text: str


class AssistRequest(BaseModel):
    prompt: str
    mode: str = "default"


# --- AI Models ---
grammar_model = AutoModelForSeq2SeqLM.from_pretrained("vennify/t5-base-grammar-correction")
grammar_tokenizer = AutoTokenizer.from_pretrained("vennify/t5-base-grammar-correction")
grammar_corrector = pipeline("text2text-generation", model=grammar_model, tokenizer=grammar_tokenizer)

summarizer = pipeline("summarization", model="google/pegasus-xsum")

writing_model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-neo-125M")
writing_tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neo-125M")
writing_assistant = TextGenerationPipeline(model=writing_model, tokenizer=writing_tokenizer)


# --- Routes ---
@app.get("/")
def home():
    return {"message": "Welcome to AI Notes!"}


@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(email=user.email, hashed_password=get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}


@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.email}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token}


@app.get("/notes/")
def get_notes(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return db.query(Note).filter(Note.user_email == user).all()


@app.post("/notes/")
def create_note(note: NoteCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    summary = summarizer(note.content, max_length=60, min_length=15, do_sample=False)[0]["summary_text"]
    full_content = note.content + "\n\n(Summary: " + summary + ")"
    new_note = Note(title=note.title, content=full_content, user_email=user)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id, Note.user_email == user).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found or unauthorized")
    db.delete(note)
    db.commit()
    return {"detail": f"Note {note_id} deleted"}


@app.post("/correct/")
def correct_grammar(request: CorrectionRequest, user: str = Depends(get_current_user)):
    prompt = "gec: " + request.text
    result = grammar_corrector(prompt, max_length=512, do_sample=False)
    return {"corrected_text": result[0]["generated_text"]}


@app.post("/assist/")
def generate_assist(request: AssistRequest, user: str = Depends(get_current_user)):
    templates = {
        "default": request.prompt,
        "email": f"Write a polite and professional email about: {request.prompt}",
        "idea": f"Brainstorm creative ideas for: {request.prompt}",
        "casual": f"Write casually about: {request.prompt}",
    }
    formatted_prompt = templates.get(request.mode.lower(), request.prompt)
    output = writing_assistant(formatted_prompt, max_length=100, do_sample=True, temperature=0.8)
    return {"completion": output[0]["generated_text"].strip()}



