import random
from hotel import *


# The order of name_suffixes is important. It should be sorted in descending
# order, using the length of the suffix with periods removed.
name_suffixes = [
    'Sisters of Our Lady of Charity of the Good Shepherd',
    'Sisters of Holy Names of Jesus and Mary',
    'Sisters of Holy Names of Jesus & Mary',
    'United States Marine Corps Reserve',
    'Certified Fund Raising Executive',
    'United States Air Force Reserve',
    'Doctor of Veterinary Medicine',
    'Society of Holy Child Jesus',
    'Certified Public Accountant',
    'United States Navy Reserve',
    'United States Marine Corps',
    'United States Army Reserve',
    'Sister of Saint Mary Order',
    'Registered Nurse Clinician',
    'Congregation of Holy Cross',
    'Chartered Life Underwriter',
    'United States Coast Guard',
    'Doctor of Dental Medicine',
    'Doctor of Dental Surgery',
    'United States Air Force',
    'Doctor of Chiropractic',
    'Protestant Episcopal',
    'Order of St Benedict',
    'Sisters of St. Joseph',
    'Doctor of Philosophy',
    'Doctor of Osteopathy',
    'Doctor of Education',
    'Blessed Virgin Mary',
    'Doctor of Optometry',
    'United States Navy',
    'United States Army',
    'Doctor of Divinity',
    'Doctor of Medicine',
    'Society of Jesus',
    'Registered Nurse',
    'Police Constable',
    'Post Commander',
    'Doctor of Laws',
    'Past Commander',
    'Incorporated',
    'Juris Doctor',
    'The Fourth',
    'The Second',
    'The Third',
    'The First',
    'the 4th',
    'the 3rd',
    'the 2nd',
    'the 1st',
    'Retired',
    'Limited',
    'Esquire',
    'Senior',
    'Junior',
    'USMCR',
    'USAFR',
    'USNR',
    'USMC',
    'USCG',
    'USAR',
    'USAF',
    'S.S.M.O.',
    'S.N.J.M.',
    'S.H.C.J.',
    'CFRE',
    'USN',
    'USA',
    'R.N.C.',
    'R.G.S',
    'Ret.',
    'O.S.B.',
    'Ltd.',
    'LL.D.',
    'Inc.',
    'Ed.D.',
    'D.V.M.',
    'C.S.J.',
    'C.S.C.',
    'CPA',
    'CLU',
    'B.V.M.',
    'Ph.D.',
    'D.M.D.',
    'D.D.S.',
    '4th',
    '3rd',
    '2nd',
    '1st',
    'III',
    'Esq.',
    'S.J.',
    'R.N.',
    'P.E.',
    'P.C.',
    'D.D.',
    'D.C.',
    'O.D.',
    'M.D.',
    'J.D.',
    'D.O.',
    'Sr.',
    'Jr.',
    'IV',
    'II']

normalized_name_suffixes = [re.sub(r'[,\.]', '', s.lower()) for s in name_suffixes]


def _generate_hotel_pin():
    """
    Returns a 7 digit number formatted as a zero padded string.
    """
    return '{:07d}'.format(random.randint(0, 9999999))


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

    # The PIN/password used by third party hotel reservervation systems
    hotel_pin = Column(UnicodeText, nullable=True, default=_generate_hotel_pin)

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
        return bool(c.SHIFTS_CREATED and self.hotel_nights and not self.is_dept_head and self.takes_shifts)

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
        return not self.placeholder and self.food_restrictions_filled_out and self.shirt_info_marked \
            and (not self.hotel_eligible or self.hotel_requests or not c.BEFORE_ROOM_DEADLINE)

    @property
    def hotel_nights(self):
        try:
            return self.hotel_requests.nights
        except:
            return []

    @property
    def hotel_nights_without_shifts_that_day(self):
        if not self.hotel_requests:
            return []

        hotel_nights = set(self.hotel_requests.nights_ints)
        shift_nights = set()
        for shift in self.shifts:
            start_time = shift.job.start_time.astimezone(c.EVENT_TIMEZONE)
            shift_night = getattr(c, start_time.strftime('%A').upper())
            shift_nights.add(shift_night)
        discrepancies = hotel_nights.difference(shift_nights)
        return list(sorted(discrepancies, key=c.NIGHT_DISPLAY_ORDER.index))

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
            legal_name = re.sub(r'\s+', ' ', self.legal_name.strip())
            last_name = re.sub(r'\s+', ' ', self.last_name.strip())
            low_legal_name = legal_name.lower()
            low_last_name = last_name.lower()
            if low_legal_name.endswith(low_last_name):
                # Catches 95% of the cases.
                return legal_name[:-len(last_name)].strip()
            else:
                norm_legal_name = re.sub(r'[,\.]', '', low_legal_name)
                norm_last_name = re.sub(r'[,\.]', '', low_last_name)
                # Before iterating through all the suffixes, check to make
                # sure the last name is even part of the legal name.
                start_index = norm_legal_name.rfind(norm_last_name)
                if start_index >= 0:
                    actual_suffix = norm_legal_name[start_index + len(norm_last_name):].strip()
                    for suffix in normalized_name_suffixes:
                        actual_suffix = re.sub(suffix, '', actual_suffix).strip()
                        if not actual_suffix:
                            index = low_legal_name.rfind(low_last_name)
                            if index >= 0:
                                return legal_name[:index].strip()
                            # Should never get here, but if we do, we should
                            # stop iterating because none of the remaining
                            # suffixes will match.
                            break
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
            legal_name = re.sub(r'\s+', ' ', self.legal_name.strip())
            legal_first_name = re.sub(r'\s+', ' ', self.legal_first_name.strip())
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
    updated    = Column(UTCDateTime, server_default=utcnow(), onupdate=utcnow())
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
