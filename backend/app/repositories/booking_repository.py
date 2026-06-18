import uuid
from typing import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session


    async def create(self, booking: Booking) -> Booking:
        self._session.add(booking)
        await self._session.commit()
        await self._session.refresh(booking)
        
        return booking


    async def get_by_id(self, booking_id: uuid.UUID) -> Booking | None:
        result = await self._session.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        
        return result.scalar_one_or_none()


    async def list(
        self,
        status: BookingStatus | None,
        page: int,
        size: int,
    ) -> tuple[Sequence[Booking], int]:
        query = select(Booking)
        count_query = select(func.count(Booking.id))

        if status is not None:
            query = query.where(Booking.status == status)
            count_query = count_query.where(Booking.status == status)

        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(Booking.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self._session.execute(query)
        
        return result.scalars().all(), total


    async def update_status(
        self,
        booking_id: uuid.UUID,
        status: BookingStatus,
    ) -> Booking | None:
        await self._session.execute(
            update(Booking)
            .where(Booking.id == booking_id)
            .values(status=status)
        )
        await self._session.commit()
        
        return await self.get_by_id(booking_id)


    async def delete(self, booking: Booking) -> None:
        await self._session.delete(booking)
        await self._session.commit()
