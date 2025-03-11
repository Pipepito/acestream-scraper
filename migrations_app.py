import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize app with basic config
app = Flask(__name__)

# Set SQLite URI - use only '/config' path, not '/app/config'
if os.environ.get('DOCKER_ENVIRONMENT'):
    db_path = '/config/acestream.db'
else:
    db_path = os.path.join(os.path.dirname(__file__), 'config', 'acestream.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Migrate directly here to avoid circular imports
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models to ensure they're registered with SQLAlchemy
from app.models import AcestreamChannel, ScrapedURL, Setting