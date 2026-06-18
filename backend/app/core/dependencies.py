from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.repositories.booking_repository import BookingRepository
from app.services.booking_service import BookingService


def get_booking_repository(session: AsyncSession = Depends(get_db)) -> BookingRepository:
    return BookingRepository(session)


def get_booking_service(
    repo: BookingRepository = Depends(get_booking_repository),
) -> BookingService:
    return BookingService(repo)
