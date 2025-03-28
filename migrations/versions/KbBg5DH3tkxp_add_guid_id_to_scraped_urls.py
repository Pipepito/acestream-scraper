"""add guid id to scraped urls

Revision ID: KbBg5DH3tkxp
Revises: t36GeaTCrBqm
Create Date: 2023-12-02

"""
from alembic import op
import sqlalchemy as sa
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'KbBg5DH3tkxp'
down_revision = 't36GeaTCrBqm'
branch_labels = None
depends_on = None

def has_column(table, column):
    """Check if column exists in table"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns(table)]
    return column in columns

def get_column_type(table, column):
    """Get type information for a column"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    for col in inspector.get_columns(table):
        if col['name'] == column:
            return col['type']
    return None

def get_dialect():
    """Get the dialect of the current database connection"""
    return op.get_bind().dialect.name

def upgrade():
    connection = op.get_bind()
    dialect = get_dialect()
    
    # Check if the id column exists
    has_id = has_column('scraped_urls', 'id')
    
    if has_id:
        # It exists - check its type
        id_type = get_column_type('scraped_urls', 'id')
        
        # If it's not already a UUID/string, convert it
        if not isinstance(id_type, (sa.String, UUID)):
            # Create a temporary UUID column
            with op.batch_alter_table('scraped_urls') as batch_op:
                batch_op.add_column(sa.Column('temp_guid', sa.String(36), nullable=True))
            
            # Generate UUIDs for all rows
            rows = connection.execute(text('SELECT id, url FROM scraped_urls')).fetchall()
            for row in rows:
                id_val, url = row
                new_guid = str(uuid.uuid4())
                connection.execute(
                    text("UPDATE scraped_urls SET temp_guid = :guid WHERE id = :id"),
                    {"guid": new_guid, "id": id_val}
                )
            
            # For SQLite (which doesn't support dropping primary keys directly), 
            # we'll recreate the table without the primary key constraint
            with op.batch_alter_table('scraped_urls', recreate='always') as batch_op:
                # Drop the id column (this implicitly removes the primary key in SQLite)
                batch_op.drop_column('id')
                
                # Rename temp_guid to id
                batch_op.alter_column('temp_guid', new_column_name='id', nullable=False)
                
                # Create new primary key constraint
                batch_op.create_primary_key('pk_scraped_urls', ['id'])
    else:
        # The id column doesn't exist yet, add it
        with op.batch_alter_table('scraped_urls') as batch_op:
            batch_op.add_column(sa.Column('id', sa.String(36), nullable=True))
        
        # If the URL was previously the primary key, generate a GUID for each row
        rows = connection.execute(text('SELECT url FROM scraped_urls')).fetchall()
        for row in rows:
            url = row[0]
            new_guid = str(uuid.uuid4())
            connection.execute(
                text("UPDATE scraped_urls SET id = :guid WHERE url = :url"),
                {"guid": new_guid, "url": url}
            )
        
        # Make the id column the primary key and not nullable
        # For SQLite, we'll recreate the table to add the primary key
        with op.batch_alter_table('scraped_urls', recreate='always') as batch_op:
            # Alter the id column to be not nullable
            batch_op.alter_column('id', nullable=False)
            
            # Create new primary key on id column
            batch_op.create_primary_key('pk_scraped_urls', ['id'])

def downgrade():
    connection = op.get_bind()
    dialect = get_dialect()
    
    # Check if the id column exists and is a string (UUID)
    if has_column('scraped_urls', 'id'):
        id_type = get_column_type('scraped_urls', 'id')
        
        if isinstance(id_type, (sa.String, UUID)):
            # Convert back to integer id
            with op.batch_alter_table('scraped_urls') as batch_op:
                batch_op.add_column(sa.Column('temp_id', sa.Integer, nullable=True))
            
            # Generate sequential IDs
            rows = connection.execute(text('SELECT id, url FROM scraped_urls ORDER BY url')).fetchall()
            for i, row in enumerate(rows, 1):
                guid_val, url = row
                connection.execute(
                    text("UPDATE scraped_urls SET temp_id = :id WHERE id = :guid"),
                    {"id": i, "guid": guid_val}
                )
            
            # For SQLite, recreate the table to change the primary key
            with op.batch_alter_table('scraped_urls', recreate='always') as batch_op:
                # Drop the GUID id column
                batch_op.drop_column('id')
                
                # Rename temp_id to id and make it the primary key
                batch_op.alter_column('temp_id', new_column_name='id', nullable=False)
                batch_op.create_primary_key('pk_scraped_urls', ['id'])
