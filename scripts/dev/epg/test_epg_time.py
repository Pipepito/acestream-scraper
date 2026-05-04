from app import create_app
from app.services.epg_service import EPGService

def test_parse_times():
    """Test the EPG time parsing with different formats."""
    app = create_app()
    with app.app_context():
        epg_service = EPGService()
        
        # Test various formats
        test_cases = [
            # Format with space
            "20250526064200 +0200",
            # Format without space
            "20250526064200+0200",
            # Format with no timezone (should be treated as UTC)
            "20250526064200",
            # DavidMuma's format
            "20250528142500 +0200",
            # Test another timezone
            "20250526064200 -0500",
            # Test another timezone without space
            "20250526064200-0500"
        ]
        
        print("Testing EPG time parsing:")
        print("-" * 40)
        
        for test_case in test_cases:
            result = epg_service._parse_xmltv_time(test_case)
            print(f"Input:  {test_case}")
            print(f"Output: {result} (UTC: {result.strftime('%Y-%m-%d %H:%M:%S %Z')})")
            print(f"ISO:    {result.isoformat()}")
            print("-" * 40)

if __name__ == "__main__":
    test_parse_times()
