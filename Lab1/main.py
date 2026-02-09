from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import engine, Base
from app.routes import users, games, trade_offers
from app.schemas.schemas import Error

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Video Game Exchange API",
    description="RESTful API for exchanging retro video games between users",
    version="1.0.0"
)

app.include_router(users.router)
app.include_router(games.router)
app.include_router(trade_offers.router)


@app.get("/", tags=["root"])
def read_root():
    """Root endpoint with API information"""
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
    """Convert HTTP exceptions to JSON error responses"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Convert validation errors to JSON error responses"""
    return JSONResponse(
        status_code=400,
        content={"code": 400, "message": "Validation error", "details": str(exc)}
    )
