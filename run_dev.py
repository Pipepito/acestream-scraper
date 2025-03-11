#!/usr/bin/env python
import os
import sys
import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Ensure project root is in Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Ensure config directory exists
    config_dir = Path(project_root) / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensuring config directory exists: {config_dir}")
    
    # Set development environment
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_APP'] = 'app'
    
    try:
        # Import the create_app function and create the app
        from app import create_app
        app = create_app()
        
        # Run the development server
        app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()