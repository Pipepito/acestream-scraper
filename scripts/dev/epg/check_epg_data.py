"""
Check database for EPG data
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_epg_data():
    """Check EPG data in database"""
    from app import create_app
    from app.models.epg_source import EPGSource
    from app.models.epg_channel import EPGChannel
    from app.models.epg_program import EPGProgram
    from app.models.tv_channel import TVChannel
    
    app = create_app()
    
    with app.app_context():
        # Check EPG sources
        sources = EPGSource.query.all()
        print(f"\n=== EPG SOURCES ({len(sources)}) ===")
        for source in sources:
            print(f"ID: {source.id} | Name: {source.name} | Enabled: {source.enabled}")
            print(f"URL: {source.url}")
            print(f"Last updated: {source.last_updated}")
            print("-" * 40)
        
        # Check EPG channels
        channels = EPGChannel.query.all()
        print(f"\n=== EPG CHANNELS ({len(channels)}) ===")
        if channels:
            for i, channel in enumerate(channels[:5], 1):  # Show first 5
                print(f"{i}. ID: {channel.id} | Name: {channel.name}")
                print(f"   XML ID: {channel.channel_xml_id} | Source ID: {channel.epg_source_id}")
            
            if len(channels) > 5:
                print(f"... and {len(channels) - 5} more channels")
        else:
            print("No EPG channels found in database")
        
        # Check EPG programs
        programs = EPGProgram.query.all()
        print(f"\n=== EPG PROGRAMS ({len(programs)}) ===")
        if programs:
            for i, program in enumerate(programs[:5], 1):  # Show first 5
                print(f"{i}. ID: {program.id} | Title: {program.title}")
                print(f"   Channel ID: {program.epg_channel_id}")
                print(f"   Time: {program.start_time} - {program.end_time}")
            
            if len(programs) > 5:
                print(f"... and {len(programs) - 5} more programs")
        else:
            print("No EPG programs found in database")
        
        # Check TV channels with EPG IDs
        tv_channels = TVChannel.query.filter(TVChannel.epg_id.isnot(None)).all()
        print(f"\n=== TV CHANNELS WITH EPG IDS ({len(tv_channels)}) ===")
        if tv_channels:
            for i, channel in enumerate(tv_channels[:5], 1):  # Show first 5
                print(f"{i}. ID: {channel.id} | Name: {channel.name}")
                print(f"   EPG ID: {channel.epg_id}")
            
            if len(tv_channels) > 5:
                print(f"... and {len(tv_channels) - 5} more channels")
        else:
            print("No TV channels with EPG IDs found in database")
        
        return {
            'sources_count': len(sources),
            'channels_count': len(channels),
            'programs_count': len(programs),
            'tv_channels_with_epg_count': len(tv_channels)
        }

if __name__ == "__main__":
    check_epg_data()
