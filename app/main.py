from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import uuid
from typing import List
from app.tasks import TaskCreate, TaskUpdate, Task
from app.auth import (
    fake_users_db, get_password_hash, authenticate_user,
    create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES,
    Token, get_current_user, User,
)
import os
from dotenv import load_dotenv

load_dotenv()  # will look for a .env file

app = FastAPI(title="QuickTask API")

@app.get("/")
async def health_check():
    return {"message": "QuickTask API is up and running!"}

@app.post("/auth/register", response_model=User, tags=["auth"])
async def register(form: OAuth2PasswordRequestForm = Depends()):
    if form.username in fake_users_db:
        raise HTTPException(400, "Username already registered")
    fake_users_db[form.username] = {
        "username": form.username,
        "hashed_password": get_password_hash(form.password),
    }
    return User(username=form.username)


@app.post("/auth/token", response_model=Token, tags=["auth"])
async def login_for_token(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(401, "Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


# example protected route
@app.get("/users/me", response_model=User, tags=["users"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


from app.tasks import (
    fake_tasks_db,
    TaskCreate,
    TaskUpdate,
    Task,
)
from app.auth import get_current_user, User

# Create a task
@app.post("/tasks", response_model=Task, tags=["tasks"])
async def create_task(
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
):
    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        owner=current_user.username,
        **payload.dict()
    )
    fake_tasks_db[task_id] = task.dict()
    return task

# List tasks
@app.get("/tasks", response_model=List[Task], tags=["tasks"])
async def list_tasks(current_user: User = Depends(get_current_user)):
    return [
        Task(**t)
        for t in fake_tasks_db.values()
        if t["owner"] == current_user.username
    ]

# Get single task
@app.get("/tasks/{task_id}", response_model=Task, tags=["tasks"])
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    t = fake_tasks_db.get(task_id)
    if not t or t["owner"] != current_user.username:
        raise HTTPException(404, "Task not found")
    return Task(**t)

# Update task
@app.patch("/tasks/{task_id}", response_model=Task, tags=["tasks"])
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
):
    t = fake_tasks_db.get(task_id)
    if not t or t["owner"] != current_user.username:
        raise HTTPException(404, "Task not found")
    updated = t.copy()
    for field, val in payload.dict(exclude_unset=True).items():
        updated[field] = val
    fake_tasks_db[task_id] = updated
    return Task(**updated)

# Delete task
@app.delete("/tasks/{task_id}", status_code=204, tags=["tasks"])
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    t = fake_tasks_db.get(task_id)
    if not t or t["owner"] != current_user.username:
        raise HTTPException(404, "Task not found")
    del fake_tasks_db[task_id]