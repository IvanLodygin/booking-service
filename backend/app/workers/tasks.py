import logging
import random
import uuid

from celery import Task
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.booking import Booking, BookingStatus
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
_engine = create_engine(_sync_url, pool_pre_ping=True)
_SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)

FAILURE_PROBABILITY = 0.15


def _set_status(booking_id: uuid.UUID, status: BookingStatus) -> None:
    with _SessionLocal() as session:
        session.execute(
            update(Booking)
            .where(Booking.id == booking_id)
            .values(status=status)
        )
        session.commit()


@celery_app.task(
    bind=True,
    name="booking_service.confirm_booking",
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    acks_late=True,
)
def confirm_booking(self: Task, booking_id: str) -> dict:
    bid = uuid.UUID(booking_id)

    with _SessionLocal() as session:
        booking = session.get(Booking, bid)
        if booking is None:
            logger.warning("confirm_booking: booking not found", extra={"booking_id": booking_id})
            return {"status": "not_found", "booking_id": booking_id}

        if booking.status != BookingStatus.PENDING:
            logger.info(
                "confirm_booking: idempotent skip",
                extra={"booking_id": booking_id, "current_status": booking.status},
            )
            return {"status": "skipped", "booking_id": booking_id, "current_status": booking.status.value}

    if random.random() < FAILURE_PROBABILITY:
        if self.request.retries >= self.max_retries:
            _set_status(bid, BookingStatus.FAILED)
            logger.error(
                "confirm_booking: external service failed, all retries exhausted",
                extra={"booking_id": booking_id},
            )
            return {"status": "failed", "booking_id": booking_id}

        logger.warning(
            "confirm_booking: external service error, retrying",
            extra={
                "booking_id": booking_id,
                "attempt": self.request.retries + 1,
                "max_retries": self.max_retries,
            },
        )
        raise self.retry(exc=RuntimeError("External service unavailable"))

    _set_status(bid, BookingStatus.CONFIRMED)
    logger.info(
        "confirm_booking: notification sent",
        extra={"booking_id": booking_id, "event": "mock_notification_sent"},
    )
    return {"status": "confirmed", "booking_id": booking_id}
