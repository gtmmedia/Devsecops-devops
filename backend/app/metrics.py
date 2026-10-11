"""Custom Prometheus metrics (business metrics on top of the HTTP metrics).

HTTP request count / latency come from prometheus-fastapi-instrumentator.
Here we add:
  quickdesk_tickets_created_total   counter, incremented on POST /api/tickets
  quickdesk_comments_created_total  counter, incremented on POST .../comments
  quickdesk_tickets{status="..."}   gauge, computed from the DB at scrape time
"""

from collections.abc import Callable, Iterator

from prometheus_client import REGISTRY, Counter
from prometheus_client.core import GaugeMetricFamily
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import STATUSES, Ticket

TICKETS_CREATED = Counter("quickdesk_tickets_created", "Tickets created since the process started")
COMMENTS_CREATED = Counter(
    "quickdesk_comments_created", "Comments created since the process started"
)


class TicketGaugeCollector:
    """Asks the database for ticket counts every time Prometheus scrapes."""

    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def collect(self) -> Iterator[GaugeMetricFamily]:
        gauge = GaugeMetricFamily(
            "quickdesk_tickets",
            "Tickets currently stored, by status",
            labels=["status"],
        )
        try:
            with self.session_factory() as session:
                rows = session.execute(
                    select(Ticket.status, func.count()).group_by(Ticket.status)
                ).all()
        except Exception:  # DB down: skip the gauge, keep /metrics alive
            return
        counts = dict(rows)
        for status in STATUSES:
            gauge.add_metric([status], counts.get(status, 0))
        yield gauge


collector = TicketGaugeCollector(SessionLocal)
REGISTRY.register(collector)
