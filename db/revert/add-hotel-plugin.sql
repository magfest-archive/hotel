-- Revert hotel:add-hotel-plugin from pg

BEGIN;

DROP TABLE hotel_requests;

DROP TABLE room;

DROP TABLE room_assignment;

ALTER TABLE attendee
        DROP COLUMN hotel_eligible;

COMMIT;
