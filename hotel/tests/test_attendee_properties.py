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
