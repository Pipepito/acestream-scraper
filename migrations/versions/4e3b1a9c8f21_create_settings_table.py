"""Create settings table

Revision ID: create_settings_table
Create Date: 2025-03-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import json
import os
from pathlib import Path


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


def upgrade():
    # Create settings table if it doesn't exist
    op.create_table(
        'settings',
        sa.Column('key', sa.String(128), nullable=False),
        sa.Column('value', sa.String(4096), nullable=True),
        sa.PrimaryKeyConstraint('key')
    )
    
    # Get existing config values
    config = load_existing_config()
    
    # Insert settings from existing config using raw SQL for maximum compatibility
    op.execute(
        f"INSERT INTO settings (key, value) VALUES ('base_url', '{config['base_url']}')"
    )
    op.execute(
        f"INSERT INTO settings (key, value) VALUES ('ace_engine_url', '{config['ace_engine_url']}')"
    )
    op.execute(
        f"INSERT INTO settings (key, value) VALUES ('rescrape_interval', '{config['rescrape_interval']}')"
    )
    op.execute(
        "INSERT INTO settings (key, value) VALUES ('setup_completed', 'true')"
    )
    op.execute(
        f"INSERT INTO settings (key, value) VALUES ('setup_timestamp', '{sa.func.now()}')"
    )


def downgrade():
    op.drop_table('settings')