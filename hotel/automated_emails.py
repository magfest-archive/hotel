from hotel import *

AutomatedEmail.queries[Room] = lambda session: session.query(Room).options(subqueryload(Room.assignments).subqueryload(RoomAssignment.attendee))

# add subqueryload to existing query
orig_query = AutomatedEmail.queries[Attendee]
AutomatedEmail.queries[Attendee] = lambda session: orig_query(session).options(subqueryload(Attendee.hotel_requests))

AutomatedEmail(Attendee, 'Want volunteer hotel room space at {EVENT_NAME}?', 'hotel_rooms.txt',
           lambda a: c.AFTER_SHIFTS_CREATED and a.hotel_eligible, sender=c.ROOM_EMAIL_SENDER,
           when=days_before(45, c.ROOM_DEADLINE, 14))

AutomatedEmail(Attendee, 'Reminder to sign up for {EVENT_NAME} hotel room space', 'hotel_reminder.txt',
           lambda a: a.hotel_eligible and not a.hotel_requests, sender=c.ROOM_EMAIL_SENDER,
               when=days_before(14, c.ROOM_DEADLINE, 2))

AutomatedEmail(Attendee, 'Last chance to sign up for {EVENT_NAME} hotel room space', 'hotel_reminder.txt',
           lambda a: a.hotel_eligible and not a.hotel_requests, sender=c.ROOM_EMAIL_SENDER,
               when=days_before(2, c.ROOM_DEADLINE))

AutomatedEmail(Attendee, 'Reminder to meet your {EVENT_NAME} hotel room requirements', 'hotel_hours.txt',
           lambda a: a.hotel_shifts_required and a.weighted_hours < c.HOTEL_REQ_HOURS, sender=c.ROOM_EMAIL_SENDER,
               when=days_before(14, c.FINAL_EMAIL_DEADLINE, 7))

AutomatedEmail(Attendee, 'Final reminder to meet your {EVENT_NAME} hotel room requirements', 'hotel_hours.txt',
           lambda a: a.hotel_shifts_required and a.weighted_hours < c.HOTEL_REQ_HOURS, sender=c.ROOM_EMAIL_SENDER,
               when=days_before(7, c.FINAL_EMAIL_DEADLINE))

AutomatedEmail(Room, '{EVENT_NAME} Hotel Room Assignment', 'room_assignment.txt', lambda r: r.locked_in,
               sender=c.ROOM_EMAIL_SENDER)
