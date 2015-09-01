-- Verify hotel:add-hotel-plugin on pg

BEGIN;

SELECT column_name FROM information_schema.columns WHERE table_name = 'attendee' AND column_name = 'hotel_eligible';
SELECT * from room_assignment;
SELECT * from room;
SELECT * from hotel_requests;

ROLLBACK;
