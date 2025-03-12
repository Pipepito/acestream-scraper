"""Create settings table

Revision ID: 4e3b1a9c8f21
"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path
import os
import json
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '4e3b1a9c8f21'
down_revision = 'channel_status_fields_02'
branch_labels = None
depends_on = None


def get_config_path():
    """Determine config path based on environment."""
    if os.environ.get('DOCKER_ENVIRONMENT'):
        config_path = Path('/app/config')
    else:
        # Go two directories up from migrations/versions
        base_path = Path(__file__).resolve().parent.parent.parent
        config_path = base_path / 'config'
    return config_path / 'config.json'


def load_existing_config():
    """Load configuration from existing JSON file if available."""
    config_file = get_config_path()
    default_config = {
        "base_url": "acestream://",
        "ace_engine_url": "http://127.0.0.1:6878",
        "rescrape_interval": 24
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Ensure we have the necessary keys with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception:
            pass
            
    return default_config


def has_table(table_name):
    """Check if a table exists"""
    conn = op.get_bind()
    insp = Inspector.from_engine(conn)
    return table_name in insp.get_table_names()


def has_setting(key):
    """Check if a setting exists"""
    conn = op.get_bind()
    result = conn.execute(f"SELECT COUNT(*) FROM settings WHERE key = '{key}'").scalar()
    return result > 0


def upgrade():
    if not has_table('settings'):
        # Create settings table
        op.create_table(
            'settings',
            sa.Column('key', sa.String(128), nullable=False),
            sa.Column('value', sa.String(4096), nullable=True),
            sa.PrimaryKeyConstraint('key')
        )
        
        # Get existing config values
        config = load_existing_config()
        
        # Insert settings safely
        settings_to_insert = [
            ('base_url', config['base_url']),
            ('ace_engine_url', config['ace_engine_url']),
            ('rescrape_interval', str(config['rescrape_interval'])),
            ('setup_completed', 'true'),
            ('setup_timestamp', sa.func.now())
        ]
        
        for key, value in settings_to_insert:
            if not has_setting(key):
                op.execute(
                    f"INSERT INTO settings (key, value) VALUES ('{key}', '{value}')"
                )


def downgrade():
    if has_table('settings'):
        op.drop_table('settings')