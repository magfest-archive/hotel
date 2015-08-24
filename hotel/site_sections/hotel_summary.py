from hotel import *


@all_renderable(c.PEOPLE)
class Root:
    def setup_teardown(self):
        attendees = []
        for hr in session.query(HotelRequests).filter_by(approved=True).options(joinedload(HotelRequests.attendee)).all():
            if hr.setup_teardown and hr.attendee.takes_shifts:
                reasons = []
                if hr.attendee.setup_hotel_approved and not any([shift.job.is_setup for shift in hr.attendee.shifts]):
                    reasons.append('has no setup shifts')
                if hr.attendee.teardown_hotel_approved and not any([shift.job.is_teardown for shift in hr.attendee.shifts]):
                    reasons.append('has no teardown shifts')
                if reasons:
                    attendees.append([hr.attendee, reasons])
        attendees = sorted(attendees, key=lambda tup: tup[0].full_name)

        return {
            'attendees': [
                ('Department Heads', [tup for tup in attendees if tup[0].is_dept_head]),
                ('Regular Staffers', [tup for tup in attendees if not tup[0].is_dept_head])
            ]
        }
