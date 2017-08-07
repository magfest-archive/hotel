from hotel import *


def _night(name):
    day = getattr(c, name.upper())

    def lookup(self):
        return day if day in self.nights_ints else ''
    lookup.__name__ = name
    lookup = property(lookup)

    def setter(self, val):
        if val:
            self.nights = '{},{}'.format(self.nights, day).strip(',')
        else:
            self.nights = ','.join([str(night) for night in self.nights_ints if night != day])
    setter.__name__ = name

    return lookup.setter(setter)


class NightsMixin(object):
    @property
    def nights_labels(self):
        ordered = sorted(self.nights_ints, key=c.NIGHT_DISPLAY_ORDER.index)
        return [c.NIGHTS[val] for val in ordered]

    @property
    def nights_display(self):
        return ' / '.join(self.nights_labels)

    @property
    def setup_teardown(self):
        return any(night for night in self.nights_ints if night not in c.CORE_NIGHTS)

    locals().update({mutate(name): _night(mutate(name)) for name in c.NIGHT_NAMES for mutate in [str.upper, str.lower]})


@Session.model_mixin
class Attendee:
    hotel_eligible = Column(Boolean, default=False, admin_only=True)
    hotel_requests = relationship('HotelRequests', backref=backref('attendee', load_on_pending=True), uselist=False)
    room_assignments  = relationship('RoomAssignment', backref=backref('attendee', load_on_pending=True))

    @presave_adjustment
    def staffer_hotel_eligibility(self):
        if self.badge_type == c.STAFF_BADGE:
            self.hotel_eligible = True

    @presave_adjustment
    def staffer_setup_teardown(self):
        if self.setup_hotel_approved:
            self.can_work_setup = True
        if self.teardown_hotel_approved:
            self.can_work_teardown = True

    @property
    def hotel_shifts_required(self):
        return bool(c.SHIFTS_CREATED and self.hotel_nights and c.DEPT_HEAD_RIBBON not in self.ribbon_ints and self.takes_shifts)

    @property
    def setup_hotel_approved(self):
        hr = self.hotel_requests
        return bool(hr and hr.approved and set(hr.nights_ints).intersection(c.SETUP_NIGHTS))

    @property
    def teardown_hotel_approved(self):
        hr = self.hotel_requests
        return bool(hr and hr.approved and set(hr.nights_ints).intersection(c.TEARDOWN_NIGHTS))

    @property
    def shift_prereqs_complete(self):
        return not self.placeholder and self.food_restrictions_filled_out and self.shirt_size_marked \
            and (not self.hotel_eligible or self.hotel_requests or not c.BEFORE_ROOM_DEADLINE)

    @property
    def hotel_nights(self):
        try:
            return self.hotel_requests.nights
        except:
            return []

    @cached_property
    def hotel_status(self):
        hr = self.hotel_requests
        if not hr:
            return 'Has not filled out volunteer checklist'
        elif not hr.nights:
            return 'Declined hotel space'
        elif hr.setup_teardown:
            return 'Hotel nights: {} ({})'.format(hr.nights_display, 'approved' if hr.approved else 'not yet approved')
        else:
            return 'Hotel nights: ' + hr.nights_display

    @property
    def legal_first_name(self):
        """
        Hotel exports need split legal names, but we don't collect split legal names, so we're going to have to guess.

        Returns one of the following:
            The first part of the legal name, if the legal name ends with the last name
            The first part of the legal name before a space, if the legal name has multiple parts
            The legal name itself, if the legal name is one word -- this is because attendees are more likely to use a
                different first name than their legal name, so might just enter, e.g., "Victoria" for their legal name
            The first name, if there is no legal name
        """
        if self.legal_name:
            legal_name = self.legal_name.strip()
            last_name = self.last_name.strip()
            if legal_name.lower().endswith(last_name.lower()):
                return legal_name[:-len(last_name)].strip()
            else:
                return legal_name.split(' ', 1)[0] if ' ' in legal_name else legal_name

        return self.first_name

    @property
    def legal_last_name(self):
        """
        Hotel exports need split legal names, but we don't collect split legal names, so we're going to have to guess.

        Returns one of the following:
            The second part of the legal name, if the legal name starts with the legal first name
            The second part of the legal name after a space, if the legal name has multiple parts
            The last name, if there is no legal name or if the legal name is just one word
        """
        if self.legal_name:
            legal_name = self.legal_name.strip()
            legal_first_name = self.legal_first_name.strip()
            if legal_name.lower().startswith(legal_first_name.lower()):
                return legal_name[len(legal_first_name):].strip()
            elif ' ' in legal_name:
                return legal_name.split(' ', 1)[1]
        return self.last_name


class HotelRequests(MagModel, NightsMixin):
    attendee_id        = Column(UUID, ForeignKey('attendee.id'), unique=True)
    nights             = Column(MultiChoice(c.NIGHT_OPTS))
    wanted_roommates   = Column(UnicodeText)
    unwanted_roommates = Column(UnicodeText)
    special_needs      = Column(UnicodeText)
    approved           = Column(Boolean, default=False, admin_only=True)

    def decline(self):
        self.nights = ','.join(night for night in self.nights.split(',') if int(night) in c.CORE_NIGHTS)

    @presave_adjustment
    def cascading_save(self):
        self.attendee.presave_adjustments()

    def __repr__(self):
        return '<{self.attendee.full_name} Hotel Requests>'.format(self=self)


class Room(MagModel, NightsMixin):
    notes      = Column(UnicodeText)
    message    = Column(UnicodeText)
    locked_in  = Column(Boolean, default=False)
    nights     = Column(MultiChoice(c.NIGHT_OPTS))
    created    = Column(UTCDateTime, server_default=utcnow())
    assignments = relationship('RoomAssignment', backref='room')

    @property
    def email(self):
        return [ra.attendee.email for ra in self.assignments]

    @property
    def first_names(self):
        return [ra.attendee.first_name for ra in self.assignments]

    @property
    def check_in_date(self):
        return c.NIGHT_DATES[self.nights_labels[0]]

    @property
    def check_out_date(self):
        # TODO: undo this kludgy workaround by fully implementing https://github.com/magfest/hotel/issues/39
        if self.nights_labels[-1] == 'Monday':
            return c.ESCHATON.date() + timedelta(days=1)
        else:
            return c.NIGHT_DATES[self.nights_labels[-1]] + timedelta(days=1)


class RoomAssignment(MagModel):
    room_id     = Column(UUID, ForeignKey('room.id'))
    attendee_id = Column(UUID, ForeignKey('attendee.id'))
