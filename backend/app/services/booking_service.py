import math
import uuid

from app.models.booking import Booking, BookingStatus
from app.repositories.booking_repository import BookingRepository
from app.schemas.booking import BookingCreate, BookingListResponse, BookingResponse


class BookingNotFound(Exception):
    pass


class BookingCannotBeCancelled(Exception):
    pass


class BookingService:
    def __init__(self, repository: BookingRepository) -> None:
        self._repo = repository


    async def create(self, data: BookingCreate) -> Booking:
        booking = Booking(
            name=data.name,
            datetime=data.datetime,
            service_type=data.service_type,
            status=BookingStatus.PENDING,
        )
        
        return await self._repo.create(booking)


    async def get(self, booking_id: uuid.UUID) -> Booking:
        booking = await self._repo.get_by_id(booking_id)
        
        if booking is None:
            raise BookingNotFound(booking_id)
        
        return booking


    async def list(
        self,
        status: BookingStatus | None,
        page: int,
        size: int,
    ) -> BookingListResponse:
        bookings, total = await self._repo.list(status=status, page=page, size=size)
        pages = math.ceil(total / size) if size else 1
        
        return BookingListResponse(
            items=[BookingResponse.model_validate(b) for b in bookings],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )


    async def cancel(self, booking_id: uuid.UUID) -> Booking:
        booking = await self._repo.get_by_id(booking_id)
        
        if booking is None:
            raise BookingNotFound(booking_id)
        
        if booking.status != BookingStatus.PENDING:
            raise BookingCannotBeCancelled(booking_id)
        
        await self._repo.delete(booking)
        
        return booking
