"""Ticket and comment endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app import metrics
from app.database import get_db
from app.models import Comment, Ticket
from app.schemas import (
    CommentCreate,
    CommentOut,
    Priority,
    StatsOut,
    Status,
    TicketCreate,
    TicketDetail,
    TicketOut,
    TicketSummary,
    TicketUpdate,
)

router = APIRouter(prefix="/api", tags=["tickets"])


def _get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Ticket {ticket_id} not found")
    return ticket


# ---------------------------------------------------------------- tickets ---


@router.post("/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    metrics.TICKETS_CREATED.inc()
    return ticket


@router.get("/tickets", response_model=list[TicketSummary])
def list_tickets(
    status_filter: Status | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Ticket, func.count(Comment.id))
        .outerjoin(Comment, Comment.ticket_id == Ticket.id)
        .group_by(Ticket.id)
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Ticket.title.ilike(like), Ticket.description.ilike(like)))

    result = []
    for ticket, comment_count in db.execute(stmt).all():
        summary = TicketSummary.model_validate(ticket)
        summary.comment_count = comment_count
        result.append(summary)
    return result


@router.get("/tickets/stats", response_model=StatsOut)
def ticket_stats(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Ticket.status, func.count()).group_by(Ticket.status)).all())
    high_open = db.scalar(
        select(func.count()).where(
            Ticket.priority == "high", Ticket.status.in_(("open", "in_progress"))
        )
    )
    return StatsOut(
        total=sum(counts.values()),
        open=counts.get("open", 0),
        in_progress=counts.get("in_progress", 0),
        resolved=counts.get("resolved", 0),
        closed=counts.get("closed", 0),
        high_priority_open=high_open or 0,
    )


@router.get("/tickets/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.scalar(
        select(Ticket).options(selectinload(Ticket.comments)).where(Ticket.id == ticket_id)
    )
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Ticket {ticket_id} not found")
    return ticket


@router.put("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = _get_ticket_or_404(db, ticket_id)
    # Business rule: a closed ticket is frozen until someone reopens it.
    if ticket.status == "closed" and payload.status == "closed":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Closed tickets can't be edited. Reopen the ticket first.",
        )
    for field, value in payload.model_dump().items():
        setattr(ticket, field, value)
    ticket.assignee = ticket.assignee or None  # empty string means "unassigned"
    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = _get_ticket_or_404(db, ticket_id)
    db.delete(ticket)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------- comments ---


@router.get("/tickets/{ticket_id}/comments", response_model=list[CommentOut])
def list_comments(ticket_id: int, db: Session = Depends(get_db)):
    _get_ticket_or_404(db, ticket_id)
    return db.scalars(
        select(Comment).where(Comment.ticket_id == ticket_id).order_by(Comment.id)
    ).all()


@router.post(
    "/tickets/{ticket_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(ticket_id: int, payload: CommentCreate, db: Session = Depends(get_db)):
    _get_ticket_or_404(db, ticket_id)
    comment = Comment(ticket_id=ticket_id, **payload.model_dump())
    db.add(comment)
    db.commit()
    db.refresh(comment)
    metrics.COMMENTS_CREATED.inc()
    return comment
