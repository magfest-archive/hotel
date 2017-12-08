from uber.utils import noon_datetime
from hotel import *


@all_renderable(c.PEOPLE)
class Root:
    # TODO: handle people who didn't request setup / teardown but who were assigned to a setup / teardown room
    def setup_teardown(self, session):
        attendees = []
        for hr in (session.query(HotelRequests)
                          .filter_by(approved=True)
                          .options(joinedload(HotelRequests.attendee).subqueryload(Attendee.shifts).joinedload(Shift.job))):
            if hr.setup_teardown and hr.attendee.takes_shifts and hr.attendee.badge_status in [c.NEW_STATUS, c.COMPLETED_STATUS]:
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

    @csv_file
    def inconsistent_shoulder_shifts(self, out, session):
        query = session.query(Attendee).join(HotelRequests) \
            .options(
                subqueryload(Attendee.shifts).subqueryload(Shift.job).subqueryload(Job.department),
                subqueryload(Attendee.hotel_requests)) \
            .filter(HotelRequests.approved == True)

        shoulder_nights_missing_shifts = defaultdict(lambda: defaultdict(list))

        for attendee in query:
            if attendee.is_dept_head:
                continue
            approved_nights = set(attendee.hotel_requests.nights_ints)
            approved_regular_nights = approved_nights.intersection(c.CORE_NIGHTS)
            approved_shoulder_nights = approved_nights.difference(c.CORE_NIGHTS)
            shifts_by_night = defaultdict(list)
            departments = set()
            for shift in attendee.shifts:
                job = shift.job
                dept = job.department
                departments.add(dept)
                start_time = job.start_time.astimezone(c.EVENT_TIMEZONE)
                shift_night = getattr(c, start_time.strftime('%A').upper())
                shifts_by_night[shift_night].append(shift)

                if start_time < noon_datetime(start_time):
                    day_before = start_time - timedelta(days=1)
                    shift_night = getattr(c, day_before.strftime('%A').upper())
                    shifts_by_night[shift_night].append(shift)

            discrepencies = approved_shoulder_nights.difference(set(shifts_by_night.keys()))
            if discrepencies:
                for dept in departments:
                    shoulder_nights_missing_shifts[dept][attendee] = list(discrepencies)

        rows = []
        departments = set(shoulder_nights_missing_shifts.keys())
        for dept in sorted(departments, key=lambda d: d.name):
            for attendee in sorted(shoulder_nights_missing_shifts[dept], key=lambda a: a.full_name):
                nights = shoulder_nights_missing_shifts[dept][attendee]
                night_names = ' / '.join([c.NIGHTS[n] for n in c.NIGHT_DISPLAY_ORDER if n in nights])
                rows.append([dept.name, attendee.full_name, attendee.email, night_names])

        out.writerow(['Department', 'Attendee', 'Attendee Email', 'Inconsistent Nights'])
        for row in rows:
            out.writerow(row)
