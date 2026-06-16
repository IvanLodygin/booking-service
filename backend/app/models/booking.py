from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime,  Enum as SQLAlchemyEnum
from app.core.db.base import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Booking(Base):
    __tablename__ = 'bookings'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(255))
    service_type: Mapped[str] = mapped_column(String(255))
    datetime: Mapped[DateTime] = mapped_column(DateTime)
    
    status: Mapped[BookingStatus] = mapped_column(
        SQLAlchemyEnum(BookingStatus),
        default=BookingStatus.PENDING,
        index=True
    )