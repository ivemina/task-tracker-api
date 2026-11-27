from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
import os
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal
from models import TaskModel, UserModel
from security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

app = FastAPI()
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    completed: bool | None = None


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    completed: bool = False


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> UserModel:
    credentials_error = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_error
    user = db.get(UserModel, user_id)
    if user is None:
        raise credentials_error
    return user


def find_task(db: Session, task_id: int, user: UserModel) -> TaskModel:
    task = db.scalar(
        select(TaskModel).where(
            TaskModel.id == task_id, TaskModel.owner_id == user.id
        )
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    task = TaskModel(
        title=payload.title,
        description=payload.description,
        owner_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/tasks", response_model=list[Task])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return db.scalars(
        select(TaskModel)
        .where(TaskModel.owner_id == current_user.id)
        .order_by(TaskModel.id)
    ).all()


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return find_task(db, task_id, current_user)


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    task = find_task(db, task_id, current_user)
    updates = payload.model_dump(exclude_unset=True)
    if "title" in updates and updates["title"] is None:
        raise HTTPException(status_code=422, detail="title cannot be null")
    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    task = find_task(db, task_id, current_user)
    db.delete(task)
    db.commit()


@app.post("/users", response_model=UserRead, status_code=201)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    email = payload.email.lower()
    existing = db.scalar(select(UserModel).where(UserModel.email == email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = UserModel(email=email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.scalar(select(UserModel).where(UserModel.email == form.username.lower()))
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id), token_type="bearer")


@app.get("/users/me", response_model=UserRead)
def read_me(current_user: UserModel = Depends(get_current_user)):
    return current_user