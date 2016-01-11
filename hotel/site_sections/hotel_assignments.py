from hotel import *


@all_renderable(c.STAFF_ROOMS)
class Root:
    def index(self, session):
        attendee = session.admin_attendee()
        three_days_before = (c.EPOCH - timedelta(days=3)).strftime('%A')
        two_days_before = (c.EPOCH - timedelta(days=2)).strftime('%A')
        day_before = (c.EPOCH - timedelta(days=1)).strftime('%A')
        last_day = c.ESCHATON.strftime('%A')
        return {
            'dump': _hotel_dump(session),
            'nights': [{
                'core': False,
                'name': three_days_before.lower(),
                'val': getattr(c, three_days_before.upper()),
                'desc': three_days_before + ' night (for super-early setup volunteers)'
            }, {
                'core': False,
                'name': two_days_before.lower(),
                'val': getattr(c, two_days_before.upper()),
                'desc': two_days_before + ' night (for early setup volunteers)'
            }, {
                'core': False,
                'name': day_before.lower(),
                'val': getattr(c, day_before.upper()),
                'desc': day_before + ' night (for setup volunteers)'
            }] + [{
                'core': True,
                'name': c.NIGHTS[night].lower(),
                'val': night,
                'desc': c.NIGHTS[night]
            } for night in c.CORE_NIGHTS] + [{
                'core': False,
                'name': last_day.lower(),
                'val': getattr(c, last_day.upper()),
                'desc': last_day + ' night (for teardown volunteers)'
            }]
        }

    @ajax
    def create_room(self, session, **params):
        params['nights'] = list(filter(bool, [params.pop(night, None) for night in c.NIGHT_NAMES]))
        session.add(session.room(params))
        session.commit()
        return _hotel_dump(session)

    @ajax
    def edit_room(self, session, **params):
        params['nights'] = list(filter(bool, [params.pop(night, None) for night in c.NIGHT_NAMES]))
        session.room(params)
        session.commit()
        return _hotel_dump(session)

    @ajax
    def delete_room(self, session, id):
        room = session.room(id)
        session.delete(room)
        session.commit()
        return _hotel_dump(session)

    @ajax
    def lock_in_room(self, session, id):
        room = session.room(id)
        room.locked_in = True
        session.commit()
        return _hotel_dump(session)

    @ajax
    def assign_to_room(self, session, attendee_id, room_id):
        message = ''
        room = session.room(room_id)
        for other in session.query(RoomAssignment).filter_by(attendee_id=attendee_id).all():
            if set(other.room.nights_ints).intersection(room.nights_ints):
                message = "Warning: this attendee already has a room which overlaps with this room's nights"
        else:
            attendee = session.attendee(attendee_id)
            ra = RoomAssignment(attendee=attendee, room=room)
            session.add(ra)
            hr = attendee.hotel_requests
            if room.setup_teardown:
                hr.approved = True
            elif not hr.approved:
                hr.decline()
            session.commit()
        return dict(_hotel_dump(session), message=message)

    @ajax
    def unassign_from_room(self, session, attendee_id, room_id):
        for ra in session.query(RoomAssignment).filter_by(attendee_id=attendee_id, room_id=room_id).all():
            session.delete(ra)
        session.commit()
        return _hotel_dump(session)

    @csv_file
    def ordered(self, out, session):
        reqs = [hr for hr in session.query(HotelRequests).options(joinedload(HotelRequests.attendee)).all() if hr.nights and hr.attendee.badge_status in (c.NEW_STATUS, c.COMPLETED_STATUS)]
        assigned = {ra.attendee for ra in session.query(RoomAssignment).options(joinedload(RoomAssignment.attendee), joinedload(RoomAssignment.room)).all()}
        unassigned = {hr.attendee for hr in reqs if hr.attendee not in assigned}

        names = {}
        for attendee in unassigned:
            names.setdefault(attendee.last_name.lower(), set()).add(attendee)

        lookup = defaultdict(set)
        for xs in names.values():
            for attendee in xs:
                lookup[attendee] = xs

        for req in reqs:
            if req.attendee in unassigned:
                for word in req.wanted_roommates.lower().replace(',', '').split():
                    try:
                        combined = lookup[list(names[word])[0]] | lookup[req.attendee]
                        for attendee in combined:
                            lookup[attendee] = combined
                    except:
                        pass

        writerow = lambda a, hr: out.writerow([
            a.full_name, a.email, a.cellphone,
            a.hotel_requests.nights_display, ' / '.join(a.assigned_depts_labels),
            hr.wanted_roommates, hr.unwanted_roommates, hr.special_needs
        ])
        grouped = {frozenset(group) for group in lookup.values()}
        out.writerow(['Name', 'Email', 'Phone', 'Nights', 'Departments', 'Roomate Requests', 'Roomate Anti-Requests', 'Special Needs'])
        # TODO: for better efficiency, a multi-level joinedload would be preferable here
        for room in session.query(Room).options(joinedload(Room.assignments)).all():
            for i in range(3):
                out.writerow([])
            out.writerow([('Locked-in ' if room.locked_in else '') + 'room created by STOPS for ' + room.nights_display + (' ({})'.format(room.notes) if room.notes else '')])
            for ra in room.assignments:
                writerow(ra.attendee, ra.attendee.hotel_requests)
        for group in sorted(grouped, key=len, reverse=True):
            for i in range(3):
                out.writerow([])
            for a in group:
                writerow(a, a.hotel_requests)

    @csv_file
    def passkey(self, out, session):
        """spreadsheet in the format requested by the Hilton Mark Center"""
        out.writerow(['Last Name', 'First Name', 'Arrival', 'Departure', 'Room Type', 'Number of Adults', 'Credit Card Name', 'Credit Card Number', 'Credit Card Expiration', 'Last Name 2', 'First Name 2', 'Last Name 3', 'First Name 3', 'Last Name 4', 'First Name 4', 'comments'])
        for room in session.query(Room).order_by(Room.created).all():
            if room.assignments:
                assignments = [ra.attendee for ra in room.assignments[:4]]
                roommates = [[a.last_name, a.first_name] for a in assignments[1:]] + [['', '']] * (4 - len(assignments))
                out.writerow([
                    assignments[0].last_name,
                    assignments[0].first_name,
                    room.check_in_date.strftime('%Y-%m-%d'),
                    room.check_out_date.strftime('%Y-%m-%d'),
                    'Q2',  # code for two beds, 'K1' would indicate a single king-sized bed
                    len(assignments),
                    '', '', ''  # no credit card info in this spreadsheet
                ] + sum(roommates, []) + [room.notes])


def _attendee_dict(attendee):
    return {
        'id': attendee.id,
        'name': attendee.full_name,
        'nights': getattr(attendee.hotel_requests, 'nights_display', ''),
        'special_needs': getattr(attendee.hotel_requests, 'special_needs', ''),
        'wanted_roommates': getattr(attendee.hotel_requests, 'wanted_roommates', ''),
        'unwanted_roommates': getattr(attendee.hotel_requests, 'unwanted_roommates', ''),
        'approved': int(getattr(attendee.hotel_requests, 'approved', False)),
        'departments': ' / '.join(attendee.assigned_depts_labels),
        'nights_lookup': {night: getattr(attendee.hotel_requests, night, False) for night in c.NIGHT_NAMES},
        'multiply_assigned': len(attendee.room_assignments) > 1
    }


def _room_dict(room):
    return dict({
        'id': room.id,
        'notes': room.notes,
        'message': room.message,
        'locked_in': room.locked_in,
        'nights': room.nights_display,
        'attendees': [_attendee_dict(ra.attendee) for ra in sorted(room.assignments, key=lambda ra: ra.attendee.full_name)]
    }, **{
        night: getattr(room, night) for night in c.NIGHT_NAMES
    })


def _get_declined(session):
    return [_attendee_dict(a) for a in session.query(Attendee)
                                              .order_by(Attendee.full_name)
                                              .join(Attendee.hotel_requests)
                                              .filter(Attendee.hotel_requests != None,
                                                      HotelRequests.nights == '',
                                                      Attendee.badge_status.in_([c.NEW_STATUS, c.COMPLETED_STATUS])).all()]


def _get_unconfirmed(session, assigned_ids):
    return [_attendee_dict(a) for a in session.query(Attendee)
                                              .order_by(Attendee.full_name)
                                              .filter(Attendee.hotel_eligible == True,
                                                      Attendee.hotel_requests == None,
                                                      Attendee.badge_status.in_([c.NEW_STATUS, c.COMPLETED_STATUS])).all()
                              if a not in assigned_ids]


def _get_unassigned(session, assigned_ids):
    return [_attendee_dict(a) for a in session.query(Attendee)
                                              .order_by(Attendee.full_name)
                                              .join(Attendee.hotel_requests)
                                              .filter(Attendee.hotel_requests != None,
                                                      HotelRequests.nights != '',
                                                      Attendee.badge_status.in_([c.NEW_STATUS, c.COMPLETED_STATUS])).all()
                              if a.id not in assigned_ids]


def _hotel_dump(session):
    rooms = [_room_dict(room) for room in session.query(Room).order_by(Room.locked_in.desc(), Room.created).all()]
    assigned = sum([r['attendees'] for r in rooms], [])
    assigned_ids = [a['id'] for a in assigned]
    unassigned = _get_unassigned(session, assigned_ids)
    return {
        'rooms': rooms,
        'assigned': assigned,
        'unassigned': unassigned,
        'declined': _get_declined(session),
        'unconfirmed': _get_unconfirmed(session, assigned_ids),
        'eligible': sorted(assigned + unassigned, key=lambda a: a['name'])
    }
