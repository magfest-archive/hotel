from hotel import *

# MAGFest provides staff rooms for returning volunteers.  Add a "room_deadline" setting to the [dates]
# section of the main repo's config when including this plugin.

StopsEmail('Want volunteer hotel room space at {EVENT_NAME}?', 'hotel_rooms.txt',
           lambda a: days_before(45, c.ROOM_DEADLINE, 14) and c.AFTER_SHIFTS_CREATED and a.hotel_eligible)

StopsEmail('Reminder to sign up for {EVENT_NAME} hotel room space', 'hotel_reminder.txt',
           lambda a: days_before(14, c.ROOM_DEADLINE, 2) and a.hotel_eligible and not a.hotel_requests)

StopsEmail('Last chance to sign up for {EVENT_NAME} hotel room space', 'hotel_reminder.txt',
           lambda a: days_before(2, c.ROOM_DEADLINE) and a.hotel_eligible and not a.hotel_requests)

StopsEmail('Reminder to meet your {EVENT_NAME} hotel room requirements', 'hotel_hours.txt',
           lambda a: days_before(14, c.UBER_TAKEDOWN, 7) and a.hotel_shifts_required and a.weighted_hours < 30)

StopsEmail('Final reminder to meet your {EVENT_NAME} hotel room requirements', 'hotel_hours.txt',
           lambda a: days_before(7, c.UBER_TAKEDOWN) and a.hotel_shifts_required and a.weighted_hours < 30)
