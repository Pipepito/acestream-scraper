"""update acestream channel source url

Revision ID: ZgB93dF5Rt7p
Revises: KbBg5DH3tkxp
Create Date: 2023-12-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect

# revision identifiers, used by Alembic.
revision = 'ZgB93dF5Rt7p'
down_revision = 'KbBg5DH3tkxp'
branch_labels = None
depends_on = None

def get_foreign_keys(conn, table_name):
    """Get all foreign keys for a table"""
    inspector = inspect(conn)
    return inspector.get_foreign_keys(table_name)

def upgrade():
    # Get connection
    connection = op.get_bind()
    
    # First, check if the table has foreign keys (for SQLite compatibility)
    foreign_keys = get_foreign_keys(connection, 'acestream_channels')
    
    # Find if there's a foreign key on source_url
    source_url_fk = None
    for fk in foreign_keys:
        if 'source_url' in fk['constrained_columns']:
            source_url_fk = fk
            break
            
    # SQLite doesn't support dropping constraints directly - we need to recreate the table
    # Use batch_alter_table which handles the table reconstruction for SQLite
    # This will implicitly drop all foreign keys when recreating the table
    with op.batch_alter_table('acestream_channels', recreate='always') as batch_op:
        # Add the new scraped_url_id column
        batch_op.add_column(sa.Column('scraped_url_id', sa.Integer(), nullable=True))
        
        # Note: The foreign key on source_url is implicitly dropped because we're recreating the table
        # No need to explicitly drop it with SQLite

    # Migrate data - populate scraped_url_id from source_url
    channels = connection.execute(text(
        "SELECT id, source_url FROM acestream_channels WHERE source_url IS NOT NULL"
    )).fetchall()
    
    # For each channel, find matching scraped_url and update scraped_url_id
    for channel_id, source_url in channels:
        # Find matching scraped URL
        scraped_url = connection.execute(text(
            "SELECT id FROM scraped_urls WHERE url = :url"
        ), {"url": source_url}).fetchone()
        
        if scraped_url:
            # Update the channel with the found scraped_url_id
            connection.execute(text(
                "UPDATE acestream_channels SET scraped_url_id = :url_id WHERE id = :channel_id"
            ), {"url_id": scraped_url[0], "channel_id": channel_id})
    
    # Add the new foreign key constraint for scraped_url_id
    with op.batch_alter_table('acestream_channels', recreate='always') as batch_op:
        batch_op.create_foreign_key(
            'fk_acestream_channels_scraped_url_id_scraped_urls',
            'scraped_urls',
            ['scraped_url_id'], ['id']
        )


def downgrade():
    # Get connection
    connection = op.get_bind()
    
    # SQLite doesn't support dropping constraints directly
    # Use batch_alter_table which handles the table reconstruction
    with op.batch_alter_table('acestream_channels', recreate='always') as batch_op:
        # Drop the foreign key constraint by recreating the table without it
        # Then drop the column
        batch_op.drop_column('scraped_url_id')
        
        # Re-add foreign key on source_url to restore original schema
        batch_op.create_foreign_key(
            'fk_acestream_channels_source_url_scraped_urls',
            'scraped_urls',
            ['source_url'], ['url']
        )
