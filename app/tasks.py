# app/tasks.py

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: datetime
    reminders: List[int] = Field(default_factory=list)  # seconds before deadline


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    reminders: Optional[List[int]] = None
    status: Optional[str] = None


class TaskOut(TaskBase):
    id: str
    owner: str
    status: str

    class Config:
        from_attributes = True

    @field_validator("reminders", mode="before")
    @classmethod
    def _split_reminders(cls, v):
        # if coming from ORM, v might be a comma‑string
        if isinstance(v, str):
            return [int(x) for x in v.split(",") if x]
        return v
