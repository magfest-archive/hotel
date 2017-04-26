"""Initial migration

Revision ID: 771555241255
Revises: 1ed43776064f
Create Date: 2017-04-24 09:15:59.549855

"""


# revision identifiers, used by Alembic.
revision = '771555241255'
down_revision = '1ed43776064f'
branch_labels = ('hotel',)
depends_on = None

from alembic import op
import sqlalchemy as sa
import sideboard.lib.sa


try:
    is_sqlite = op.get_context().dialect.name == 'sqlite'
except:
    is_sqlite = False

if is_sqlite:
    op.get_context().connection.execute('PRAGMA foreign_keys=ON;')
    utcnow_server_default = "(datetime('now', 'utc'))"
else:
    utcnow_server_default = "timezone('utc', current_timestamp)"


def upgrade():
    op.create_table('room',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('notes', sa.Unicode(), server_default='', nullable=False),
    sa.Column('message', sa.Unicode(), server_default='', nullable=False),
    sa.Column('locked_in', sa.Boolean(), server_default='False', nullable=False),
    sa.Column('nights', sa.Unicode(), server_default='', nullable=False),
    sa.Column('created', sideboard.lib.sa.UTCDateTime(), server_default=sa.text(utcnow_server_default), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_room'))
    )
    op.create_table('hotel_requests',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('attendee_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('nights', sa.Unicode(), server_default='', nullable=False),
    sa.Column('wanted_roommates', sa.Unicode(), server_default='', nullable=False),
    sa.Column('unwanted_roommates', sa.Unicode(), server_default='', nullable=False),
    sa.Column('special_needs', sa.Unicode(), server_default='', nullable=False),
    sa.Column('approved', sa.Boolean(), server_default='False', nullable=False),
    sa.ForeignKeyConstraint(['attendee_id'], ['attendee.id'], name=op.f('fk_hotel_requests_attendee_id_attendee')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_hotel_requests')),
    sa.UniqueConstraint('attendee_id', name=op.f('uq_hotel_requests_attendee_id'))
    )
    op.create_table('room_assignment',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('room_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('attendee_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['attendee_id'], ['attendee.id'], name=op.f('fk_room_assignment_attendee_id_attendee')),
    sa.ForeignKeyConstraint(['room_id'], ['room.id'], name=op.f('fk_room_assignment_room_id_room')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_room_assignment'))
    )
    op.add_column('attendee', sa.Column('hotel_eligible', sa.Boolean(), server_default='False', nullable=False))


def downgrade():
    op.drop_column('attendee', 'hotel_eligible')
    op.drop_table('room_assignment')
    op.drop_table('hotel_requests')
    op.drop_table('room')
