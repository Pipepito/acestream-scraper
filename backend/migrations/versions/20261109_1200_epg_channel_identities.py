"""Group matching EPG channels while preserving source programme ownership."""
from alembic import op
import sqlalchemy as sa

revision = '20261109_1200'
down_revision = '20261107_1200'
branch_labels = None
depends_on = None


def upgrade():
    identities = op.create_table('epg_channel_identities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('channel_xml_id', sa.String(255), nullable=False),
        sa.Column('normalized_name', sa.String(255), nullable=False),
        sa.UniqueConstraint('channel_xml_id', 'normalized_name', name='uq_epg_channel_identity'))
    # SQLite permits adding a nullable REFERENCES column without rebuilding the
    # heavily referenced memberships table (programmes/rules retain every ID).
    if op.get_bind().dialect.name == 'sqlite':
        op.execute('ALTER TABLE epg_channels ADD COLUMN identity_id INTEGER CONSTRAINT fk_epg_channel_identity REFERENCES epg_channel_identities(id)')
    else:
        op.add_column('epg_channels', sa.Column('identity_id', sa.Integer(),
            sa.ForeignKey('epg_channel_identities.id', name='fk_epg_channel_identity'), nullable=True))
    op.create_index('ix_epg_channels_identity_id', 'epg_channels', ['identity_id'])
    db = op.get_bind()
    channels = sa.table('epg_channels', sa.column('id'), sa.column('channel_xml_id'), sa.column('name'), sa.column('identity_id'))
    known = {}
    for row in db.execute(sa.select(channels.c.id, channels.c.channel_xml_id, channels.c.name)).mappings():
        key = (row['channel_xml_id'], ' '.join(row['name'].casefold().split()))
        if key not in known:
            known[key] = db.execute(identities.insert().values(channel_xml_id=key[0], normalized_name=key[1])).inserted_primary_key[0]
        db.execute(channels.update().where(channels.c.id == row['id']).values(identity_id=known[key]))


def downgrade():
    op.drop_index('ix_epg_channels_identity_id', table_name='epg_channels')
    if op.get_bind().dialect.name == 'sqlite':
        op.drop_column('epg_channels', 'identity_id')
    else:
        op.drop_constraint('fk_epg_channel_identity', 'epg_channels', type_='foreignkey')
        op.drop_column('epg_channels', 'identity_id')
    op.drop_table('epg_channel_identities')
