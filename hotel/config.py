from hotel import *

hotel_config = parse_config(__file__)
c.include_plugin_config(hotel_config)

c.NIGHT_NAMES = [name.lower() for name in c.NIGHT_VARS]
c.NIGHT_DISPLAY_ORDER = [getattr(c, night.upper()) for night in c.NIGHT_DISPLAY_ORDER]

c.NIGHT_DATES = {c.ESCHATON.strftime('%A'): c.ESCHATON.date()}

c.CORE_NIGHTS = []
_day = c.EPOCH
while _day.date() != c.ESCHATON.date():
    c.NIGHT_DATES[_day.strftime('%A')] = _day.date()
    c.CORE_NIGHTS.append(getattr(c, _day.strftime('%A').upper()))
    _day += timedelta(days=1)

for _before in range(1, 4):
    _day = c.EPOCH.date() - timedelta(days=_before)
    c.NIGHT_DATES[_day.strftime('%A')] = _day

c.SETUP_NIGHTS = c.NIGHT_DISPLAY_ORDER[:c.NIGHT_DISPLAY_ORDER.index(c.CORE_NIGHTS[0])]
c.TEARDOWN_NIGHTS = c.NIGHT_DISPLAY_ORDER[1 + c.NIGHT_DISPLAY_ORDER.index(c.CORE_NIGHTS[-1]):]

for _attr in ['CORE_NIGHT', 'SETUP_NIGHT', 'TEARDOWN_NIGHT']:
    setattr(c, _attr + '_NAMES', [c.NIGHTS[night] for night in getattr(c, _attr + 'S')])


@Config.mixin
class ExtraConfig:
    @property
    def ONE_WEEK_OR_TAKEDOWN_OR_EPOCH(self):
        week_from_now = c.EVENT_TIMEZONE.localize(datetime.combine(date.today() + timedelta(days=7), time(23, 59)))
        return min(week_from_now, c.UBER_TAKEDOWN, c.EPOCH)
