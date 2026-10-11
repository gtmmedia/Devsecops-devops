"""Pydantic models: what the API accepts and returns."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Status = Literal["open", "in_progress", "resolved", "closed"]
Priority = Literal["low", "medium", "high"]


class _Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class TicketCreate(_Base):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    priority: Priority = "medium"
    requester_name: str = Field(min_length=1, max_length=100)
    requester_email: EmailStr


class TicketUpdate(_Base):
    """PUT replaces every editable field, so all of them are required."""

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    status: Status
    priority: Priority
    assignee: str | None = Field(default=None, max_length=100)


class CommentCreate(_Base):
    author: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=5000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author: str
    body: str
    created_at: datetime


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: Status
    priority: Priority
    requester_name: str
    requester_email: str
    assignee: str | None
    created_at: datetime
    updated_at: datetime


class TicketSummary(TicketOut):
    comment_count: int = 0


class TicketDetail(TicketOut):
    comments: list[CommentOut] = []


class StatsOut(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int
    high_priority_open: int
