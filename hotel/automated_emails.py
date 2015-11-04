from hotel import *

AutomatedEmail.extra_models[Room] = lambda session: session.query(Room).all()

AutomatedEmail('Want volunteer hotel room space at {EVENT_NAME}?', 'hotel_rooms.txt',
           lambda a: days_before(45, c.ROOM_DEADLINE, 14) and c.AFTER_SHIFTS_CREATED and a.hotel_eligible, sender='MAGFest Staff Rooms <staffrooms@magfest.org>')

AutomatedEmail('Reminder to sign up for {EVENT_NAME} hotel room space', 'hotel_reminder.txt',
           lambda a: days_before(14, c.ROOM_DEADLINE, 2) and a.hotel_eligible and not a.hotel_requests, sender='MAGFest Staff Rooms <staffrooms@magfest.org>')

AutomatedEmail('Last chance to sign up for {EVENT_NAME} hotel room space', 'hotel_reminder.txt',
           lambda a: days_before(2, c.ROOM_DEADLINE) and a.hotel_eligible and not a.hotel_requests, sender='MAGFest Staff Rooms <staffrooms@magfest.org>')

AutomatedEmail('Reminder to meet your {EVENT_NAME} hotel room requirements', 'hotel_hours.txt',
           lambda a: days_before(14, c.UBER_TAKEDOWN, 7) and a.hotel_shifts_required and a.weighted_hours < c.HOTEL_REQ_HOURS, sender='MAGFest Staff Rooms <staffrooms@magfest.org>')

AutomatedEmail('Final reminder to meet your {EVENT_NAME} hotel room requirements', 'hotel_hours.txt',
           lambda a: days_before(7, c.UBER_TAKEDOWN) and a.hotel_shifts_required and a.weighted_hours < c.HOTEL_REQ_HOURS, sender='MAGFest Staff Rooms <staffrooms@magfest.org>')

AutomatedEmail(Room, '{EVENT_NAME} Hotel Room Assignment', 'room_assignment.txt', lambda r: r.locked_in,
               sender=c.ROOM_EMAIL_SENDER, sender='MAGFest Staff Rooms <staffrooms@magfest.org>')
