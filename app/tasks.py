from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

# In-memory “DB”
fake_tasks_db: Dict[str, Dict] = {}

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: datetime
    reminders: List[int] = Field(default_factory=list)  # seconds before deadline

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    deadline: Optional[datetime]
    reminders: Optional[List[int]]
    status: Optional[str]  # e.g. "pending" or "done"

class Task(TaskBase):
    id: str
    owner: str
    status: str = "pending"