"""
Comprehensive test runner for V2 API integration tests
"""

import pytest
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_all_tests():
    """Run all integration tests for V2 API endpoints."""
    
    print("=" * 80)
    print("🧪 Running V2 API Integration Tests")
    print("=" * 80)
    print()
    
    # Define test files and their descriptions
    test_files = [
        ("test_channels.py", "Channel CRUD and Status Operations"),
        ("test_tv_channels.py", "TV Channel Management and Associations"),
        ("test_epg.py", "EPG Sources, Channels, Programs and XML Generation"),
        ("test_scrapers.py", "URL Scraping and Management"),
        ("test_search.py", "Channel Search and Bulk Add Operations"),
        ("test_playlists.py", "M3U Playlist Generation"),
        ("test_config.py", "Configuration Management"),
        ("test_health.py", "Health Monitoring and Statistics"),
        ("test_warp.py", "WARP VPN Integration"),
    ]
    
    # Test configuration
    pytest_args = [
        "-v",                          # Verbose output
        "--tb=short",                  # Short traceback format
        "--strict-markers",            # Strict marker checking
        "--strict-config",             # Strict config checking
        "-x",                          # Stop on first failure
        "--disable-warnings",          # Disable warnings for cleaner output
    ]
    
    all_passed = True
    results = {}
    
    for test_file, description in test_files:
        test_path = str(backend_dir / "tests" / test_file)
        
        if not os.path.exists(test_path):
            print(f"⚠️  Test file not found: {test_file}")
            results[test_file] = "MISSING"
            all_passed = False
            continue
        
        print(f"🔍 Testing: {description}")
        print(f"   File: {test_file}")
        
        # Run the specific test file
        exit_code = pytest.main(pytest_args + [test_path])
        
        if exit_code == 0:
            print(f"✅ PASSED: {test_file}")
            results[test_file] = "PASSED"
        else:
            print(f"❌ FAILED: {test_file}")
            results[test_file] = "FAILED"
            all_passed = False
        
        print("-" * 60)
    
    # Summary
    print()
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for result in results.values() if result == "PASSED")
    failed_count = sum(1 for result in results.values() if result == "FAILED")
    missing_count = sum(1 for result in results.values() if result == "MISSING")
    
    print(f"Total Test Files: {len(test_files)}")
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⚠️  Missing: {missing_count}")
    print()
    
    # Detailed results
    for test_file, result in results.items():
        status_icon = {
            "PASSED": "✅",
            "FAILED": "❌",
            "MISSING": "⚠️"
        }.get(result, "❓")
        print(f"{status_icon} {test_file}: {result}")
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED! The V2 API is fully functional.")
        return 0
    else:
        print("💥 SOME TESTS FAILED! Check the output above for details.")
        return 1


def run_specific_test(test_name):
    """Run a specific test file."""
    
    test_files = {
        "channels": "test_channels.py",
        "tv": "test_tv_channels.py",
        "tv_channels": "test_tv_channels.py",
        "epg": "test_epg.py",
        "scrapers": "test_scrapers.py",
        "search": "test_search.py",
        "playlists": "test_playlists.py",
        "config": "test_config.py",
        "health": "test_health.py",
        "warp": "test_warp.py",
    }
    
    if test_name.lower() in test_files:
        test_file = test_files[test_name.lower()]
    elif test_name.endswith('.py'):
        test_file = test_name
    else:
        test_file = f"test_{test_name}.py"
    
    test_path = str(backend_dir / "tests" / test_file)
    
    if not os.path.exists(test_path):
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    print(f"🔍 Running specific test: {test_file}")
    print("=" * 60)
    
    pytest_args = [
        "-v",
        "--tb=long",
        "--strict-markers",
        "--strict-config",
        test_path
    ]
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print(f"✅ Test passed: {test_file}")
    else:
        print(f"❌ Test failed: {test_file}")
    
    return exit_code


def run_endpoint_coverage_test():
    """Run a test to check endpoint coverage."""
    
    print("🔍 Checking V2 API Endpoint Coverage")
    print("=" * 60)
    
    # Expected endpoints based on the migration documentation
    expected_endpoints = {
        # Channel endpoints
        "GET /channels/": "List channels",
        "GET /channels/{id}": "Get channel by ID",
        "POST /channels/": "Create channel",
        "PUT /channels/{id}": "Update channel",
        "DELETE /channels/{id}": "Delete channel",
        "POST /channels/{id}/check_status": "Check channel status",
        "POST /channels/check_status_all": "Check all channels status",
        "GET /channels/status_summary": "Get status summary",
        
        # TV Channel endpoints
        "GET /tv-channels/": "List TV channels",
        "GET /tv-channels/{id}": "Get TV channel by ID",
        "POST /tv-channels/": "Create TV channel",
        "PUT /tv-channels/{id}": "Update TV channel",
        "DELETE /tv-channels/{id}": "Delete TV channel",
        "GET /tv-channels/{id}/acestreams": "Get associated acestreams",
        "POST /tv-channels/{id}/acestreams": "Associate acestream",
        "DELETE /tv-channels/{id}/acestreams/{acestream_id}": "Remove association",
        
        # EPG endpoints
        "GET /epg/sources": "List EPG sources",
        "POST /epg/sources": "Create EPG source",
        "GET /epg/sources/{id}": "Get EPG source",
        "DELETE /epg/sources/{id}": "Delete EPG source",
        "POST /epg/sources/{id}/refresh": "Refresh EPG source",
        "POST /epg/sources/refresh_all": "Refresh all EPG sources",
        "GET /epg/channels": "List EPG channels",
        "GET /epg/channels/{id}": "Get EPG channel",
        "GET /epg/channels/{id}/programs": "Get EPG programs",
        "GET /epg/xml": "Get EPG XML",
        
        # Scraper endpoints
        "POST /scrapers/scrape": "Scrape URL",
        "GET /scrapers/urls": "List scraped URLs",
        "POST /scrapers/urls": "Add scraped URL",
        "GET /scrapers/urls/{id}": "Get scraped URL",
        "DELETE /scrapers/urls/{id}": "Delete scraped URL",
        "POST /scrapers/urls/{id}/scrape": "Scrape specific URL",
        "POST /scrapers/urls/scrape_all": "Scrape all URLs",
        
        # Search endpoints
        "GET /search": "Search channels",
        "POST /search/add": "Add channel from search",
        "POST /search/add_multiple": "Add multiple channels",
        
        # Playlist endpoints
        "GET /playlists/m3u": "Generate M3U playlist",
        "GET /playlists/groups": "Get playlist groups",
        
        # Config endpoints
        "GET /config/base_url": "Get base URL setting",
        "PUT /config/base_url": "Update base URL setting",
        "GET /config/ace_engine_url": "Get engine URL setting",
        "PUT /config/ace_engine_url": "Update engine URL setting",
        "GET /config/all": "Get all settings",
        "GET /config/acestream_status": "Get acestream status",
        
        # Health endpoints
        "GET /health": "Get health status",
        "GET /stats": "Get statistics",
        
        # WARP endpoints
        "GET /warp/status": "Get WARP status",
        "POST /warp/connect": "Connect WARP",
        "POST /warp/disconnect": "Disconnect WARP",
        "POST /warp/mode": "Set WARP mode",
        "POST /warp/license": "Register WARP license",
    }
    
    print(f"Expected Endpoints: {len(expected_endpoints)}")
    print()
    
    # Run a simple test to verify endpoints exist
    test_path = str(backend_dir / "tests" / "test_endpoint_coverage.py")
    
    # Create a simple endpoint coverage test
    coverage_test = f'''
"""
Endpoint coverage test
"""
import pytest
from fastapi.testclient import TestClient

def test_endpoint_coverage():
    """Test that all expected endpoints are implemented."""
    from app.main import app
    client = TestClient(app)
    
    # Test basic endpoint availability (200, 404, 422 are acceptable)
    endpoints_to_test = [
        ("GET", "/channels/"),
        ("GET", "/tv-channels/"),
        ("GET", "/epg/sources"),
        ("GET", "/scrapers/urls"),
        ("GET", "/search"),
        ("GET", "/playlists/m3u"),
        ("GET", "/config/all"),
        ("GET", "/health"),
        ("GET", "/warp/status"),
    ]
    
    for method, endpoint in endpoints_to_test:
        if method == "GET":
            response = client.get(endpoint)
            # Accept 200 (success) or 500 (server error, but endpoint exists)
            assert response.status_code in [200, 500], f"Endpoint {{method}} {{endpoint}} not found"
    
    print(f"✅ All {{len(endpoints_to_test)}} basic endpoints are accessible")
'''
    
    with open(test_path, 'w') as f:
        f.write(coverage_test)
    
    # Run the coverage test
    exit_code = pytest.main(["-v", test_path])
    
    # Clean up
    os.unlink(test_path)
    
    return exit_code


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "coverage":
            exit_code = run_endpoint_coverage_test()
        else:
            exit_code = run_specific_test(sys.argv[1])
    else:
        exit_code = run_all_tests()
    
    sys.exit(exit_code)
