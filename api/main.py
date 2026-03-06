# =============================================================================
# main.py — Application Entry Point
# =============================================================================
# What this file does:
#   Sets up the FastAPI app, wires in the three route modules, and attaches two
#   cross-cutting concerns: Prometheus metrics collection and Kafka shutdown.
#
# Key decisions:
#   - Prometheus Instrumentator: auto-instruments every route so we get request
#     count, latency, and status codes at /metrics with zero manual code.
#   - atexit.register: guarantees Kafka's internal message buffer is flushed
#     before the process exits — important for not losing in-flight events.
#   - Global exception handlers: normalizes all errors into a consistent JSON
#     shape { code, message } rather than FastAPI's default validation format.
# =============================================================================

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import atexit
from prometheus_fastapi_instrumentator import Instrumentator

from app.database import engine, Base
from app.routes import users, games, trade_offers
from app.schemas.schemas import Error
from app.kafka_producer import flush_kafka_producer

Base.metadata.create_all(bind=engine)

atexit.register(flush_kafka_producer)

app = FastAPI(
    title="Video Game Exchange API",
    description="RESTful API for exchanging retro video games between users",
    version="1.0.0"
)

app.include_router(users.router)
app.include_router(games.router)
app.include_router(trade_offers.router)

# Hooks into FastAPI's middleware chain to track every request automatically.
# Exposes collected metrics at GET /metrics — that's what Prometheus scrapes.
Instrumentator().instrument(app).expose(app)


@app.get("/", tags=["root"])
def read_root():
    return {
        "message": "Retro Video Game Exchange API",
        "version": "1.0.0",
        "docs": "/docs",
        "_links": {
            "self": "/",
            "users": "/users",
            "games": "/games",
            "games_search": "/games/search",
            "trade_offers": "/trade-offers",
            "docs": "/docs"
        }
    }


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"code": 400, "message": "Validation error", "details": str(exc)}
    )
