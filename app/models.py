import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    tasks = relationship("Task", back_populates="owner_rel")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner = Column(String, ForeignKey("users.username"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    deadline = Column(DateTime, nullable=False)
    # store reminders as comma‑separated ints for now
    reminders = Column(String, default="")
    status = Column(String, default="pending")

    owner_rel = relationship("User", back_populates="tasks")
