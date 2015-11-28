from hotel import *
import pytest
from sideboard.tests import patch_session


@pytest.fixture(scope='session', autouse=True)
def init_db(request):
    patch_session(Session, request)
    initialize_db()


def test_hotel_shifts_required(monkeypatch):
    monkeypatch.setattr(c, 'SHIFTS_CREATED', localized_now())
    assert not Attendee().hotel_shifts_required
    monkeypatch.setattr(Attendee, 'takes_shifts', True)
    monkeypatch.setattr(Attendee, 'hotel_nights', [c.THURSDAY, c.FRIDAY])
    assert Attendee().hotel_shifts_required
    assert not Attendee(ribbon=c.DEPT_HEAD_RIBBON).hotel_shifts_required


def test_hotel_shifts_required_preshifts(monkeypatch):
    monkeypatch.setattr(c, 'SHIFTS_CREATED', '')
    monkeypatch.setattr(Attendee, 'takes_shifts', True)
    monkeypatch.setattr(Attendee, 'hotel_nights', [c.THURSDAY, c.FRIDAY])
    assert not Attendee().hotel_shifts_required


def test_hotel_request_allows_setup_and_teardown(monkeypatch):
    with Session() as session:
        attendee = Attendee()
        session.add(attendee)
        session.commit()
        assert not attendee.can_work_setup
        assert not attendee.can_work_teardown

        hr = HotelRequests()
        hr.attendee = attendee
        session.add(hr)
        hr.nights = ','.join(map(str, [c.WEDNESDAY, c.THURSDAY, c.MONDAY]))

        attendee.hotel_requests.approve()
        session.commit()

        assert attendee.can_work_setup
        assert attendee.can_work_teardown
