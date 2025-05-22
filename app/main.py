# app/main.py

import uuid
from datetime import timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from app.db import get_db
from app.email_tasks import send_reminder_email
from app.models import Task as TaskModel
from app.models import User as UserModel
from app.tasks import TaskCreate, TaskOut, TaskUpdate

app = FastAPI(title="QuickTask API")


# -- Health check ------------------------------------------------------------


@app.get("/")
async def health_check():
    return {"message": "QuickTask API is up and running!"}


# -- Schemas ------------------------------------------------------------


class RegisterIn(BaseModel):
    username: str
    email: EmailStr
    password: str


# -- Auth Endpoints ---------------------------------------------------------


@app.post("/auth/register", response_model=User, tags=["auth"])
async def register(
    reg: RegisterIn,
    db: AsyncSession = Depends(get_db),
):
    # check username
    result = await db.execute(select(UserModel).filter_by(username=reg.username))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Username already registered")

    # check email
    result = await db.execute(select(UserModel).filter_by(email=reg.email))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    # create user
    new_user = UserModel(
        username=reg.username,
        email=reg.email,
        hashed_password=get_password_hash(reg.password),
    )
    db.add(new_user)
    await db.commit()

    return User(username=new_user.username, email=new_user.email)


@app.post("/auth/token", response_model=Token, tags=["auth"])
async def login_for_token(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(form.username, form.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me", response_model=User, tags=["users"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# -- Task Endpoints ---------------------------------------------------------


@app.post("/tasks", response_model=TaskOut, tags=["tasks"])
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # persist to DB
    db_task = TaskModel(
        id=str(uuid.uuid4()),
        owner=current_user.username,
        title=payload.title,
        description=payload.description,
        deadline=payload.deadline,
        reminders=",".join(map(str, payload.reminders)),
        status="pending",
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    # schedule reminder emails
    for seconds_before in payload.reminders:
        eta = db_task.deadline - timedelta(seconds=seconds_before)
        send_reminder_email.apply_async(
            args=[
                current_user.email,
                f"Reminder: {db_task.title}",
                f"Your task “{db_task.title}” is due at {db_task.deadline}",
            ],
            eta=eta,
        )

    return TaskOut.from_orm(db_task)


@app.get("/tasks", response_model=List[TaskOut], tags=["tasks"])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(TaskModel).filter_by(owner=current_user.username))
    tasks = result.scalars().all()
    return [TaskOut.from_orm(t) for t in tasks]


@app.get("/tasks/{task_id}", response_model=TaskOut, tags=["tasks"])
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(TaskModel).filter_by(id=task_id))
    db_task = result.scalar_one_or_none()
    if not db_task or db_task.owner != current_user.username:
        raise HTTPException(404, "Task not found")
    return TaskOut.from_orm(db_task)


@app.patch("/tasks/{task_id}", response_model=TaskOut, tags=["tasks"])
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(TaskModel).filter_by(id=task_id))
    db_task = result.scalar_one_or_none()
    if not db_task or db_task.owner != current_user.username:
        raise HTTPException(404, "Task not found")

    for field, val in payload.dict(exclude_unset=True).items():
        setattr(
            db_task, field, val if field != "reminders" else ",".join(map(str, val))
        )

    await db.commit()
    await db.refresh(db_task)
    return TaskOut.from_orm(db_task)


@app.delete("/tasks/{task_id}", status_code=204, tags=["tasks"])
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(TaskModel).filter_by(id=task_id))
    db_task = result.scalar_one_or_none()
    if not db_task or db_task.owner != current_user.username:
        raise HTTPException(404, "Task not found")
    await db.delete(db_task)
    await db.commit()
