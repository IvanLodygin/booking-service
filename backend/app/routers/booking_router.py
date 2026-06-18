import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_booking_service
from app.core.rate_limit import rate_limit
from app.models.booking import BookingStatus
from app.schemas.booking import BookingCreate, BookingListResponse, BookingResponse
from app.services.booking_service import BookingCannotBeCancelled, BookingNotFound, BookingService
from app.workers.tasks import confirm_booking

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit)],
)
async def create_booking(
    data: BookingCreate,
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    booking = await service.create(data)
    confirm_booking.delay(str(booking.id))
    
    return BookingResponse.model_validate(booking)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID,
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    try:
        booking = await service.get(booking_id)
    except BookingNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    return BookingResponse.model_validate(booking)


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    status_filter: Annotated[BookingStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    service: BookingService = Depends(get_booking_service),
) -> BookingListResponse:
    return await service.list(status=status_filter, page=page, size=size)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: uuid.UUID,
    service: BookingService = Depends(get_booking_service),
) -> None:
    try:
        await service.cancel(booking_id)
    except BookingNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    except BookingCannotBeCancelled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending bookings can be cancelled",
        )
