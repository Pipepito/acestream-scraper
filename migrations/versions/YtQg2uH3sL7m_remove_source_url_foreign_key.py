"""remove source url foreign key

Revision ID: YtQg2uH3sL7m
Revises: ZgB93dF5Rt7p
Create Date: 2023-12-16 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect

# revision identifiers, used by Alembic.
revision = 'YtQg2uH3sL7m'
down_revision = 'ZgB93dF5Rt7p'
branch_labels = None
depends_on = None

def get_foreign_keys(conn, table_name):
    """Get all foreign keys for a table"""
    inspector = inspect(conn)
    return inspector.get_foreign_keys(table_name)

def upgrade():
    # Get connection 
    connection = op.get_bind()
    
    # 1. Create a new column 'url' without foreign key constraint
    with op.batch_alter_table('acestream_channels') as batch_op:
        batch_op.add_column(sa.Column('url', sa.Text(), nullable=True))
    
    # 2. Copy data from source_url to url
    connection.execute(text("UPDATE acestream_channels SET url = source_url"))
    
    # 3. Drop the source_url column (which implicitly drops the foreign key constraint)
    with op.batch_alter_table('acestream_channels', recreate='always') as batch_op:
        batch_op.drop_column('source_url')
    
    # 4. Rename url back to source_url (now without a foreign key constraint)
    with op.batch_alter_table('acestream_channels') as batch_op:
        batch_op.alter_column('url', new_column_name='source_url')

def downgrade():
    # NOTE: This downgrade assumes all source_url values exist in scraped_urls.url
    # It may fail if data integrity is not maintained
    connection = op.get_bind()
    
    # 1. Rename source_url to url temporarily
    with op.batch_alter_table('acestream_channels') as batch_op:
        batch_op.alter_column('source_url', new_column_name='url')
    
    # 2. Add source_url column with foreign key constraint
    # Using recreate='always' to handle SQLite limitations
    with op.batch_alter_table('acestream_channels', recreate='always') as batch_op:
        batch_op.add_column(sa.Column('source_url', sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            'fk_acestream_channels_source_url_scraped_urls',
            'scraped_urls',
            ['source_url'], ['url']
        )
    
    # 3. Copy data from url to source_url (only where foreign key would be valid)
    connection.execute(text("""
        UPDATE acestream_channels 
        SET source_url = url 
        WHERE url IN (SELECT url FROM scraped_urls)
    """))
    
    # 4. Drop the temporary url column
    with op.batch_alter_table('acestream_channels') as batch_op:
        batch_op.drop_column('url')
