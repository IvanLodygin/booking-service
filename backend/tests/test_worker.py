import uuid
from unittest.mock import MagicMock, patch

from app.models.booking import Booking, BookingStatus
from app.workers.tasks import FAILURE_PROBABILITY, confirm_booking


def _make_booking(status: BookingStatus = BookingStatus.PENDING) -> Booking:
    b = Booking()
    b.id = uuid.uuid4()
    b.name = "Test User"
    b.service_type = "consultation"
    b.status = status
    return b


def _run_task(booking: Booking) -> dict:
    with (
        patch("app.workers.tasks._SessionLocal") as mock_session_cls,
        patch("app.workers.tasks._set_status") as mock_set_status,
    ):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = booking
        mock_session_cls.return_value = mock_session

        result = confirm_booking.run(str(booking.id))
        return result, mock_set_status


def test_confirm_booking_success():
    booking = _make_booking(BookingStatus.PENDING)
    with (
        patch("app.workers.tasks._SessionLocal") as mock_session_cls,
        patch("app.workers.tasks._set_status") as mock_set_status,
        patch("app.workers.tasks.random.random", return_value=0.99),
    ):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = booking
        mock_session_cls.return_value = mock_session

        result = confirm_booking.run(str(booking.id))

    assert result["status"] == "confirmed"
    mock_set_status.assert_called_once_with(booking.id, BookingStatus.CONFIRMED)


def test_confirm_booking_failure_exhausted():
    booking = _make_booking(BookingStatus.PENDING)
    with (
        patch("app.workers.tasks._SessionLocal") as mock_session_cls,
        patch("app.workers.tasks._set_status") as mock_set_status,
        patch("app.workers.tasks.random.random", return_value=0.0),
    ):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = booking
        mock_session_cls.return_value = mock_session

        task_instance = confirm_booking
        task_instance.push_request(retries=task_instance.max_retries)
        try:
            result = task_instance.run(str(booking.id))
        finally:
            task_instance.pop_request()

    assert result["status"] == "failed"
    mock_set_status.assert_called_once_with(booking.id, BookingStatus.FAILED)


def test_confirm_booking_idempotent_confirmed():
    booking = _make_booking(BookingStatus.CONFIRMED)
    with (
        patch("app.workers.tasks._SessionLocal") as mock_session_cls,
        patch("app.workers.tasks._set_status") as mock_set_status,
    ):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = booking
        mock_session_cls.return_value = mock_session

        result = confirm_booking.run(str(booking.id))

    assert result["status"] == "skipped"
    mock_set_status.assert_not_called()


def test_confirm_booking_idempotent_failed():
    booking = _make_booking(BookingStatus.FAILED)
    with (
        patch("app.workers.tasks._SessionLocal") as mock_session_cls,
        patch("app.workers.tasks._set_status") as mock_set_status,
    ):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = booking
        mock_session_cls.return_value = mock_session

        result = confirm_booking.run(str(booking.id))

    assert result["status"] == "skipped"
    mock_set_status.assert_not_called()


def test_confirm_booking_not_found():
    with (
        patch("app.workers.tasks._SessionLocal") as mock_session_cls,
        patch("app.workers.tasks._set_status") as mock_set_status,
    ):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = None
        mock_session_cls.return_value = mock_session

        result = confirm_booking.run(str(uuid.uuid4()))

    assert result["status"] == "not_found"
    mock_set_status.assert_not_called()


def test_failure_probability_constant():
    assert FAILURE_PROBABILITY == 0.15
