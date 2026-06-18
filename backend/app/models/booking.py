from datetime import datetime

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base
import enum
import uuid


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    name: Mapped[str] = mapped_column(String(255))
    service_type: Mapped[str] = mapped_column(String(255))
    datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    status: Mapped[BookingStatus] = mapped_column(
        SQLAlchemyEnum(BookingStatus, values_callable=lambda x: [e.value for e in x]),
        default=BookingStatus.PENDING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
