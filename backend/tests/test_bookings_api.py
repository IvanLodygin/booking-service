import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_booking(client: AsyncClient, booking_payload: dict, mocker):
    mocker.patch("app.routers.booking_router.confirm_booking.delay")
    response = await client.post("/bookings", json=booking_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == booking_payload["name"]
    assert data["service_type"] == booking_payload["service_type"]
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_booking_dispatches_task(client: AsyncClient, booking_payload: dict, mocker):
    mock_delay = mocker.patch("app.routers.booking_router.confirm_booking.delay")
    response = await client.post("/bookings", json=booking_payload)
    assert response.status_code == 201
    booking_id = response.json()["id"]
    mock_delay.assert_called_once_with(booking_id)


@pytest.mark.asyncio
async def test_create_booking_missing_fields(client: AsyncClient, mocker):
    mocker.patch("app.routers.booking_router.confirm_booking.delay")
    response = await client.post("/bookings", json={"name": "Ivan"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_booking_empty_name(client: AsyncClient, booking_payload: dict, mocker):
    mocker.patch("app.routers.booking_router.confirm_booking.delay")
    booking_payload["name"] = "   "
    response = await client.post("/bookings", json=booking_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_booking(client: AsyncClient, booking_payload: dict, mocker):
    mocker.patch("app.routers.booking_router.confirm_booking.delay")
    create_resp = await client.post("/bookings", json=booking_payload)
    booking_id = create_resp.json()["id"]

    response = await client.get(f"/bookings/{booking_id}")
    assert response.status_code == 200
    assert response.json()["id"] == booking_id
    assert response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_get_booking_not_found(client: AsyncClient):
    response = await client.get(f"/bookings/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_bookings(client: AsyncClient, booking_payload: dict, mocker):
    mocker.patch("app.routers.booking_router.confirm_booking.delay")
    await client.post("/bookings", json=booking_payload)
    await client.post("/bookings", json=booking_payload)

    response = await client.get("/bookings")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_list_bookings_filter_by_status(client: AsyncClient, booking_payload: dict, mocker, session):
    mocker.patch("app.routers.booking_router.confirm_booking.delay")
    await client.post("/bookings", json=booking_payload)

    response = await client.get("/bookings?status=pending")
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(b["status"] == "pending" for b in items)


@pytest.mark.asyncio
async def test_list_bookings_pagination(client: AsyncClient, booking_payload: dict, mocker):
    mocker.patch("app.routers.booking_router.confirm_booking.delay")
    for _ in range(3):
        await client.post("/bookings", json=booking_payload)

    response = await client.get("/bookings?page=1&size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
    assert data["size"] == 2


@pytest.mark.asyncio
async def test_cancel_booking(client: AsyncClient, booking_payload: dict, mocker):
    mocker.patch("app.routers.booking_router.confirm_booking.delay")
    create_resp = await client.post("/bookings", json=booking_payload)
    booking_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/bookings/{booking_id}")
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/bookings/{booking_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_booking_not_found(client: AsyncClient):
    response = await client.delete(f"/bookings/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_confirmed_booking(client: AsyncClient, booking_payload: dict, mocker, session):
    mocker.patch("app.routers.booking_router.confirm_booking.delay")
    create_resp = await client.post("/bookings", json=booking_payload)
    booking_id = create_resp.json()["id"]

    from app.models.booking import Booking, BookingStatus
    from sqlalchemy import update as sa_update
    import uuid as _uuid

    await session.execute(
        sa_update(Booking)
        .where(Booking.id == _uuid.UUID(booking_id))
        .values(status=BookingStatus.CONFIRMED)
    )
    await session.commit()

    response = await client.delete(f"/bookings/{booking_id}")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
