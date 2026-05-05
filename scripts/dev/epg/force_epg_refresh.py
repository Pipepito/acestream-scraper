"""
Force refresh of EPG data
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def force_epg_refresh():
    """Force refresh of EPG data"""
    from app import create_app
    from app.services.epg_service import refresh_epg_data, EPGService
    
    app = create_app()
    
    with app.app_context():
        print("Starting forced EPG refresh...")
        
        # Use the refresh function directly
        epg_service = EPGService()
        
        # Log the current EPG source state
        sources = epg_service.epg_source_repo.get_all()
        for source in sources:
            print(f"Source {source.id}: {source.url}")
            print(f"  Enabled: {source.enabled}")
            print(f"  Last updated: {source.last_updated}")
        
        # Force refresh by updating the source to be stale
        from datetime import datetime, timedelta
        for source in sources:
            source.last_updated = datetime.now() - timedelta(days=2)
            epg_service.epg_source_repo.update(source)
            print(f"  Set last_updated to {source.last_updated} to force refresh")
        
        # Fetch EPG data
        print("\nFetching EPG data...")
        epg_data = epg_service.fetch_epg_data()
        
        # Check results after refresh
        sources = epg_service.epg_source_repo.get_all()
        for source in sources:
            print(f"\nSource {source.id} after refresh:")
            print(f"  Last updated: {source.last_updated}")
        
        # Check for EPG channels and programs
        from app.models.epg_channel import EPGChannel
        from app.models.epg_program import EPGProgram
        
        channels_count = EPGChannel.query.count()
        programs_count = EPGProgram.query.count()
        
        print(f"\nAfter refresh: {channels_count} EPG channels, {programs_count} EPG programs")
        
        return {
            'epg_data_count': len(epg_data) if epg_data else 0,
            'channels_count': channels_count,
            'programs_count': programs_count
        }

if __name__ == "__main__":
    force_epg_refresh()
