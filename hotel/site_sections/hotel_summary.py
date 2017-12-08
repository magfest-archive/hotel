from hotel import *


def _quote(s):
    if ',' in s:
        s = '"{}"'.format(s)
    return s


def _quote_row(r):
    return [_quote(s) for s in r]


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

        # shifts_missing_nights = defaultdict(lambda: defaultdict(list))
        # nights_missing_shifts = defaultdict(lambda: defaultdict(list))
        # regular_nights_missing_shifts = defaultdict(lambda: defaultdict(list))
        shoulder_nights_missing_shifts = defaultdict(lambda: defaultdict(list))

        for attendee in query:
            if attendee.is_dept_head:
                continue
            approved_nights = set(attendee.hotel_requests.nights_ints)
            approved_regular_nights = approved_nights.intersection(c.CORE_NIGHTS)
            approved_shoulder_nights = approved_nights.difference(c.CORE_NIGHTS)
            shifts_by_night = defaultdict(list)
            departments = set()
            # for shift in attendee.shifts:
            #     job = shift.job
            #     dept = job.department
            #     departments.add(dept)
            #     start_time = job.start_time.astimezone(c.EVENT_TIMEZONE)
            #     shift_night = getattr(c, start_time.strftime('%A').upper())
            #     shifts_by_night[shift_night].append(shift)

            #     if shift_night not in approved_nights:
            #         shifts_missing_nights[dept][attendee].append(shift_night)

            # discrepencies = approved_nights.difference(set(shifts_by_night.keys()))
            # if discrepencies:
            #     for dept in departments:
            #         nights_missing_shifts[dept][attendee] = list(discrepencies)

            # discrepencies = approved_regular_nights.difference(set(shifts_by_night.keys()))
            # if discrepencies:
            #     for dept in departments:
            #         regular_nights_missing_shifts[dept][attendee] = list(discrepencies)

            discrepencies = approved_shoulder_nights.difference(set(shifts_by_night.keys()))
            if discrepencies:
                for dept in departments:
                    shoulder_nights_missing_shifts[dept][attendee] = list(discrepencies)

        # departments = set(shifts_missing_nights.keys()).union(nights_missing_shifts.keys())
        rows = []
        departments = set(shoulder_nights_missing_shifts.keys())
        for dept in sorted(departments, key=lambda d: d.name):
            dept_heads = sorted(dept.dept_heads, key=lambda a: a.full_name)
            dept_head_emails = ', '.join([
                a.full_name + (' <{}>'.format(a.email) if a.email else '') for a in dept_heads])

            # print(dept.name)

            # if dept in regular_nights_missing_shifts:
            #     print('')
            #     print('    REGULAR Approved Hotel Nights WITHOUT Shifts')
            #     for attendee in sorted(regular_nights_missing_shifts[dept], key=lambda a: a.full_name):
            #         nights = regular_nights_missing_shifts[dept][attendee]
            #         night_names = [c.NIGHTS[n] for n in c.NIGHT_DISPLAY_ORDER if n in nights]
            #         print('        {} <{}>: {}'.format(attendee.full_name, attendee.email, ', '.join(night_names)))

            if dept in shoulder_nights_missing_shifts:
                for attendee in sorted(shoulder_nights_missing_shifts[dept], key=lambda a: a.full_name):
                    nights = shoulder_nights_missing_shifts[dept][attendee]
                    night_names = ' / '.join([c.NIGHTS[n] for n in c.NIGHT_DISPLAY_ORDER if n in nights])
                    # attendee_email = attendee.full_name + (' <{}>'.format(attendee.email) if attendee.email else '')
                    rows.append(_quote_row([dept.name, dept_head_emails, attendee.full_name, attendee.email, night_names]))

            # if dept in nights_missing_shifts:
            #     print('')
            #     print('    ALL Hotel Approved Nights WITHOUT Shifts')
            #     for attendee in sorted(nights_missing_shifts[dept], key=lambda a: a.full_name):
            #         nights = nights_missing_shifts[dept][attendee]
            #         night_names = [c.NIGHTS[n] for n in c.NIGHT_DISPLAY_ORDER if n in nights]
            #         print('        {} <{}>: {}'.format(attendee.full_name, attendee.email, ', '.join(night_names)))

            # if dept in shifts_missing_nights:
            #     print('')
            #     print('    Shifts Without An Approved Hotel Night')
            #     for attendee in sorted(shifts_missing_nights[dept], key=lambda a: a.full_name):
            #         nights = shifts_missing_nights[dept][attendee]
            #         night_names = [c.NIGHTS[n] for n in c.NIGHT_DISPLAY_ORDER if n in nights]
            #         print('        {} <{}>: {}'.format(attendee.full_name, attendee.email, ', '.join(night_names)))

            # print('\n\n')

        out.writerow(['Department', 'Dept Heads', 'Attendee', 'Attendee Email', 'Inconsistent Nights'])
        for row in rows:
            out.writerow(row)
