"""
Test script to check if EPG XML is properly generated with programs.
"""
import sys
import os
import logging
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import app services and models
try:
    from app.extensions import db
    from app.services.playlist_service import PlaylistService
    from app.services.epg_service import EPGService
    from app.models.tv_channel import TVChannel
    from app.models.epg_program import EPGProgram
    from app.repositories.epg_program_repository import EPGProgramRepository
    from app.repositories.epg_channel_repository import EPGChannelRepository
    
    logger.info("Successfully imported app modules")
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

def count_tags_in_xml(xml_content, tag_name):
    """Count occurrences of a specific tag in XML content."""
    import re
    pattern = f'<{tag_name}[^>]*>'
    matches = re.findall(pattern, xml_content)
    return len(matches)

def test_epg_xml_generation():
    """Test EPG XML generation and ensure programs are included."""
    logger.info("Starting EPG XML generation test")
    
    # Create service instances
    playlist_service = PlaylistService()
    
    # Generate EPG XML with all channels
    xml_content = playlist_service.generate_epg_xml()
    
    logger.info(f"Generated EPG XML with length: {len(xml_content)} bytes")
    
    # Analyze content
    channel_count = count_tags_in_xml(xml_content, 'channel')
    program_count = count_tags_in_xml(xml_content, 'programme')
    
    logger.info(f"Channels in EPG XML: {channel_count}")
    logger.info(f"Programs in EPG XML: {program_count}")
    
    # Check database counts for comparison
    epg_channel_repo = EPGChannelRepository()
    epg_program_repo = EPGProgramRepository()
    
    db_channel_count = len(epg_channel_repo.get_all())
    
    logger.info(f"Channels in database: {db_channel_count}")
    
    # Save the XML to a file for inspection
    output_path = Path('generated_epg.xml')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    logger.info(f"EPG XML saved to {output_path.absolute()}")
    
    # Return success status
    return {
        'channel_count': channel_count,
        'program_count': program_count,
        'xml_size': len(xml_content),
        'output_file': str(output_path.absolute())
    }

if __name__ == "__main__":
    try:
        from app import create_app
        app = create_app()
        
        # Use app context for database operations
        with app.app_context():
            result = test_epg_xml_generation()
            
            print("\n----- EPG XML Generation Test Results -----")
            print(f"Channels in XML: {result['channel_count']}")
            print(f"Programs in XML: {result['program_count']}")
            print(f"XML file size: {result['xml_size']} bytes")
            print(f"Output file: {result['output_file']}")
            print("-----------------------------------------\n")
            
            if result['program_count'] == 0:
                print("⚠️ WARNING: No program data found in generated XML!")
            else:
                print("✅ SUCCESS: XML contains program data")
                
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        sys.exit(1)
