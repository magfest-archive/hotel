from hotel import *

hotel_config = parse_config(__file__)

c.NIGHT_DISPLAY_ORDER = [getattr(c, night.upper()) for night in hotel_config['night_display_order']]
c.NIGHT_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

c.CORE_NIGHTS = []
_day = c.EPOCH
while _day.date() != c.ESCHATON.date():
    c.CORE_NIGHTS.append(getattr(c, _day.strftime('%A').upper()))
    _day += timedelta(days=1)

c.SETUP_NIGHTS = c.NIGHT_DISPLAY_ORDER[:c.NIGHT_DISPLAY_ORDER.index(c.CORE_NIGHTS[0])]
c.TEARDOWN_NIGHTS = c.NIGHT_DISPLAY_ORDER[1 + c.NIGHT_DISPLAY_ORDER.index(c.CORE_NIGHTS[-1]):]

c.ROOMS_LOCKED_IN = hotel_config['rooms_locked_in']
