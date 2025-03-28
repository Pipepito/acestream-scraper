"""add url type to scraped urls

Revision ID: 123abc456def
Revises: h6s6bgh82cxa
Create Date: 2023-12-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = 't36GeaTCrBqm'
down_revision = 'h6s6bgh82cxa'
branch_labels = None
depends_on = None

Base = declarative_base()

def has_column(table, column):
    """Check if column exists in table"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns(table)]
    return column in columns

def upgrade():
    # Only add column if it doesn't already exist
    if not has_column('scraped_urls', 'url_type'):
        with op.batch_alter_table('scraped_urls') as batch_op:
            batch_op.add_column(sa.Column('url_type', sa.String(20), nullable=True))
        
        # Update existing URLs to set their type
        connection = op.get_bind()
        scraped_urls = connection.execute('SELECT url FROM scraped_urls').fetchall()
        
        for url in scraped_urls:
            url_type = 'zeronet' if (url.startswith('zero://') or 
                                    url.startswith('http://127.0.0.1:43110/') or 
                                    ':43110/' in url) else 'regular'
            connection.execute(
                f"UPDATE scraped_urls SET url_type = '{url_type}' WHERE url = {url}"
            )
        
        # Set default for new rows
        with op.batch_alter_table('scraped_urls') as batch_op:
            batch_op.alter_column('url_type', nullable=False, server_default='regular')

def downgrade():
    if has_column('scraped_urls', 'url_type'):
        with op.batch_alter_table('scraped_urls') as batch_op:
            batch_op.drop_column('url_type')
