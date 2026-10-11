"""QuickDesk FastAPI application entrypoint."""

import time

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routers import tickets

app = FastAPI(
    title="QuickDesk API",
    version=settings.app_version,
    description="A small helpdesk: file tickets, triage them, discuss, close.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)

# HTTP metrics (request count, latency) exposed at /metrics for Prometheus.
Instrumentator(
    should_group_status_codes=True,
    excluded_handlers=["/metrics", "/health", "/ready"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health", tags=["ops"])
def health():
    """Liveness: the process is up. Kubernetes restarts the pod if this fails."""
    return {"status": "ok", "version": settings.app_version, "sha": settings.git_sha}


@app.get("/ready", tags=["ops"])
def ready(db: Session = Depends(get_db)):
    """Readiness: the process can reach the database. If it can't, Kubernetes
    stops sending traffic to this pod (but does not restart it)."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(503, "Database unavailable") from exc
    return {"status": "ready"}


if settings.enable_debug_endpoints:

    @app.get("/api/debug/burn", tags=["debug"])
    def burn_cpu(ms: int = Query(default=200, ge=1, le=2000)):
        """Burn CPU for `ms` milliseconds. Only for the autoscaling demo."""
        end = time.perf_counter() + ms / 1000
        while time.perf_counter() < end:
            sum(i * i for i in range(2000))
        return {"burned_ms": ms}
