from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.core.logging.setup import configure_logging
from app.routers.booking_router import router as booking_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield


app = FastAPI(
    title="Booking Service",
    description="REST API for scheduling appointments",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(booking_router)


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {"status": "ok"}
