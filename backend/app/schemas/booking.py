from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    name: str
    datetime: datetime
    service_type: str

    @field_validator("name", "service_type")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    service_type: str
    datetime: datetime
    status: BookingStatus
    created_at: datetime
    updated_at: datetime


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    size: int
    pages: int
