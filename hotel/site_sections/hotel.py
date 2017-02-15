from hotel import *


@all_renderable(c.PEOPLE)
class Root:
    def index(self, session, department=None):
        attendee = session.admin_attendee()
        department = int(department or c.JOB_LOCATION_OPTS[0][0])
        return {
            'department': department,
            'dept_name': c.JOB_LOCATIONS[department],
            'checklist': session.checklist_status('hotel_eligible', department),
            'attendees': session.query(Attendee)
                                .filter_by(hotel_eligible=True)
                                .filter(Attendee.assigned_depts.contains(str(department)),
                                        Attendee.badge_status.in_([c.NEW_STATUS, c.COMPLETED_STATUS]))
                                .order_by(Attendee.full_name).all()
        }

    def mark_hotel_eligible(self, session, id):
        """
        Force mark a non-staffer as eligible for hotel space.
        This is outside the normal workflow, used for when we have a staffer that only has an attendee badge for
        some reason, and we want to mark them as being OK to crash in a room.
        """
        attendee = session.attendee(id)
        attendee.hotel_eligible = True
        session.commit()
        return '{} has now been overridden as being hotel eligible'.format(attendee.full_name)

    def requests(self, session, department=None):
        dept_filter = []
        requests = (session.query(HotelRequests)
                           .join(HotelRequests.attendee)
                           .options(joinedload(HotelRequests.attendee))
                           .filter(Attendee.badge_status.in_([c.NEW_STATUS, c.COMPLETED_STATUS]))
                           .order_by(Attendee.full_name).all())
        if department:
            dept_filter = [Attendee.assigned_depts.contains(department)]
            requests = [r for r in requests if r.attendee.assigned_to(department)]

        return {
            'requests': requests,
            'department': department,
            'declined_count': len([r for r in requests if r.nights == '']),
            'dept_name': 'All' if not department else c.JOB_LOCATIONS[int(department)],
            'checklist': session.checklist_status('approve_setup_teardown', department),
            'staffer_count': session.query(Attendee).filter(Attendee.hotel_eligible == True, *dept_filter).count()
        }

    def hours(self, session):
        return {'staffers': [s for s in session.query(Attendee)
                                               .filter(Attendee.hotel_eligible == True,
                                                       Attendee.badge_status.in_([c.NEW_STATUS, c.COMPLETED_STATUS]))
                                               .options(joinedload(Attendee.hotel_requests),
                                                        subqueryload(Attendee.shifts).subqueryload(Shift.job))
                                               .order_by(Attendee.full_name).all()
                               if s.hotel_shifts_required and s.weighted_hours < c.HOTEL_REQ_HOURS]}

    def no_shows(self, session):
        attendee_load = joinedload(RoomAssignment.attendee)
        staffers = [ra.attendee for ra in session.query(RoomAssignment)
                                                 .options(attendee_load.joinedload(Attendee.hotel_requests),
                                                          attendee_load.subqueryload(Attendee.room_assignments))
                                if not ra.attendee.checked_in]
        return {'staffers': sorted(staffers, key=lambda a: a.full_name)}

    @ajax
    def approve(self, session, id, approved):
        hr = session.hotel_requests(id)
        if approved == 'approved':
            hr.approved = True
        else:
            hr.decline()
        session.commit()
        return {'nights': hr.nights_display}

    @ajax
    def switch_hotel_eligibility(self, session, id, **params):
        attendee = session.query(Attendee).filter(Attendee.id == id).first()
        if attendee:
            attendee.hotel_eligible = not attendee.hotel_eligible
            session.commit()
            return True
