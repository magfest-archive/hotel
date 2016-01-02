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
            'staffer_count': session.query(Attendee).filter(Attendee.badge_type == c.STAFF_BADGE, *dept_filter).count()
        }

    def hours(self, session):
        return {'staffers': [s for s in session.query(Attendee)
                                               .filter(Attendee.badge_type == c.STAFF_BADGE,
                                                       Attendee.badge_status.in_([c.NEW_STATUS, c.COMPLETED_STATUS]))
                                               .order_by(Attendee.full_name).all()
                               if s.hotel_shifts_required and s.weighted_hours < c.HOTEL_REQ_HOURS]}

    def no_shows(self, session):
        staffers = [ra.attendee for ra in session.query(RoomAssignment).all() if not ra.attendee.checked_in]
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
