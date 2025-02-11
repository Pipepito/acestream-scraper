import os
import asyncio
from flask import Flask, Response, request
from .extensions import db
from .views.main import bp
from .tasks.manager import TaskManager
from .utils.config import Config
from .models import ScrapedURL, AcestreamChannel
import threading

# Global task manager instance
task_manager = None

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    config = Config()
    
    # Configure Flask app
    app.config['SQLALCHEMY_DATABASE_URI'] = config.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Production settings
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(bp)

    # Add direct route for m3u download
    @app.route('/list.m3u')
    def download_playlist():
        """Generate and return M3U playlist with optional refresh."""
        should_refresh = request.args.get('refresh', '').lower() == 'true'
        
        if should_refresh:
            urls = ScrapedURL.query.all()
            for url in urls:
                url.status = 'pending'
            db.session.commit()
        
        channels = AcestreamChannel.query.filter_by(status='active').all()
        
        playlist = ['#EXTM3U']
        for channel in channels:
            playlist.append(f'#EXTINF:-1,{channel.name}')
            playlist.append(f'acestream://{channel.id}')
        return Response('\n'.join(playlist), mimetype='audio/x-mpegurl')
    
    # Create tables and load initial URLs
    with app.app_context():
        db.create_all()
        
        # Load URLs from config into database
        for url in config.urls:
            existing_url = ScrapedURL.query.filter_by(url=url).first()
            if not existing_url:
                new_url = ScrapedURL(url=url, status='pending')
                db.session.add(new_url)
        
        # Commit any new URLs
        db.session.commit()
    
    return app

def run_task_manager(app):
    """Run task manager in a separate thread"""
    global task_manager
    if task_manager is None:
        task_manager = TaskManager()
        task_manager.init_app(app)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.create_task(task_manager.start())
            loop.run_forever()
        except KeyboardInterrupt:
            task_manager.stop()
            loop.stop()
            loop.close()

def main():
    """Main entry point for the application"""
    app = create_app()
    
    # Get port from environment variable or use default
    port = int(os.getenv('FLASK_PORT', 8000))
    
    # Start task manager in a separate thread
    task_thread = threading.Thread(target=run_task_manager, args=(app,))
    task_thread.daemon = True
    task_thread.start()
    
    # Run Flask app in main thread with production settings
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
    )

if __name__ == '__main__':
    main()