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


def test_by_default_no_setup_and_teardown(monkeypatch):
    with Session() as session:
        attendee = Attendee()
        attendee.presave_adjustments()
        assert not attendee.can_work_setup
        assert not attendee.can_work_teardown


def test_hotel_approved_and_can_work_setup_and_teardown(monkeypatch):
    with Session() as session:
        hr = HotelRequests()
        attendee = Attendee()

        # attendee requests shoulder nights, and we approve it
        hr.attendee = attendee
        hr.nights = ','.join(map(str, [c.WEDNESDAY, c.THURSDAY, c.MONDAY]))
        hr.approve()

        # on the next save, the attendee should be able to work setup and teardown
        hr.presave_adjustments()
        assert attendee.can_work_setup
        assert attendee.can_work_teardown
