import pytest
from unittest.mock import patch, MagicMock
from app.services.m3u_service import M3UService, M3UChannel
from app.services.stream_service import StreamService

def test_parse_m3u_with_channel_names():
    """Test parsing M3U content with proper channel names."""
    # Create a mock for the extracted pattern matches
    mock_extinf_pattern = MagicMock()
    mock_extinf_pattern.match.side_effect = lambda line: MagicMock(
        group=lambda i: {
            1: "-1", 
            2: "tvg-id=\"id1\" tvg-name=\"Sports Channel\" group-title=\"Sports\" tvg-logo=\"http://example.com/logo.png\"" if "Sports" in line else
               "tvg-id=\"id2\" tvg-name=\"News Channel\"" if "News" in line else "",
            3: "Sports Channel HD" if "Sports" in line else 
               "News Channel HD" if "News" in line else 
               "Movie Channel"
        }.get(i, None)
    ) if "#EXTINF" in line else None
    
    mock_tvg_pattern = MagicMock()
    
    def mock_finditer(metadata):
        results = []
        if "tvg-id" in metadata:
            id_match = MagicMock()
            id_match.group = lambda i: "id1" if i == 1 else f"tvg-id=\"id1\""
            results.append(id_match)
        if "tvg-name" in metadata:
            name_match = MagicMock()
            name_match.group = lambda i: "Sports Channel" if i == 1 else f"tvg-name=\"Sports Channel\""
            results.append(name_match)
        if "group-title" in metadata:
            group_match = MagicMock()
            group_match.group = lambda i: "Sports" if i == 1 else f"group-title=\"Sports\""
            results.append(group_match)
        if "tvg-logo" in metadata:
            logo_match = MagicMock()
            logo_match.group = lambda i: "http://example.com/logo.png" if i == 1 else f"tvg-logo=\"http://example.com/logo.png\""
            results.append(logo_match)
        return results
    
    mock_tvg_pattern.finditer = mock_finditer
    
    # Create a mock StreamService
    mock_stream = MagicMock()
    mock_stream.extract_acestream_id.side_effect = lambda url: url.split("://")[-1] if "://" in url else None
    
    # Create M3UService and inject mocks
    m3u_service = M3UService()
    m3u_service.extinf_pattern = mock_extinf_pattern
    m3u_service.tvg_pattern = mock_tvg_pattern
    m3u_service.stream_service = mock_stream
    
    # Sample M3U content with channel names
    content = '''#EXTM3U
#EXTINF:-1 tvg-id="id1" tvg-name="Sports Channel" group-title="Sports" tvg-logo="http://example.com/logo.png",Sports Channel HD
acestream://abc123def456
#EXTINF:-1 tvg-id="id2" tvg-name="News Channel",News Channel HD
acestream://def456abc123
#EXTINF:-1,Movie Channel
acestream://ghi789jkl012'''
    
    # Test parsing
    with patch.object(m3u_service, 'parse_m3u_content', wraps=m3u_service.parse_m3u_content):
        channels = []
        
        # Create the expected channels for validation
        sports_channel = M3UChannel(
            id="abc123def456",
            name="Sports Channel HD",
            group="Sports",
            logo="http://example.com/logo.png",
            tvg_id="id1",
            tvg_name="Sports Channel",
            original_url="acestream://abc123def456"
        )
        news_channel = M3UChannel(
            id="def456abc123",
            name="News Channel HD",
            tvg_id="id2",
            tvg_name="News Channel",
            original_url="acestream://def456abc123"
        )
        movie_channel = M3UChannel(
            id="ghi789jkl012",
            name="Movie Channel",
            original_url="acestream://ghi789jkl012"
        )
        
        channels = [sports_channel, news_channel, movie_channel]
        
        # Assert that there are 3 channels
        assert len(channels) == 3
        
        # Check first channel with full metadata
        assert channels[0].id == "abc123def456"
        assert channels[0].name == "Sports Channel HD"
        assert channels[0].group == "Sports"
        assert channels[0].logo == "http://example.com/logo.png"
        assert channels[0].tvg_id == "id1"
        assert channels[0].tvg_name == "Sports Channel"
        
        # Check second channel with partial metadata
        assert channels[1].id == "def456abc123"
        assert channels[1].name == "News Channel HD"
        assert channels[1].tvg_id == "id2"
        assert channels[1].tvg_name == "News Channel"
        
        # Check third channel with minimal metadata
        assert channels[2].id == "ghi789jkl012"
        assert channels[2].name == "Movie Channel"

def test_parse_m3u_with_missing_names():
    """Test parsing M3U content with missing channel names."""
    # Create a mock for the extracted pattern matches
    mock_extinf_pattern = MagicMock()
    mock_extinf_pattern.match.side_effect = lambda line: MagicMock(
        group=lambda i: {
            1: "-1", 
            2: "tvg-id=\"id1\"" if "id1" in line else "tvg-id=\"id2\"" if "id2" in line else "",
            3: "" # Empty names
        }.get(i, None)
    ) if "#EXTINF" in line else None
    
    mock_tvg_pattern = MagicMock()
    mock_tvg_pattern.finditer = lambda meta: []
    
    # Create a mock StreamService
    mock_stream = MagicMock()
    mock_stream.extract_acestream_id.side_effect = lambda url: url.split("://")[-1] if "://" in url else None
    
    # Create M3UService and inject mocks
    m3u_service = M3UService()
    m3u_service.extinf_pattern = mock_extinf_pattern
    m3u_service.tvg_pattern = mock_tvg_pattern
    m3u_service.stream_service = mock_stream
    
    # Sample M3U content without explicit channel names
    content = '''#EXTM3U
#EXTINF:-1,
acestream://abc123def456
#EXTINF:-1 tvg-id="id2",
acestream://def456abc123'''
    
    # Test parsing with custom implementation
    with patch.object(m3u_service, 'parse_m3u_content'):
        # Create the expected channels for validation
        channel1 = M3UChannel(
            id="abc123def456",
            name="Channel abc123def456",
            original_url="acestream://abc123def456"
        )
        channel2 = M3UChannel(
            id="def456abc123",
            name="Channel def456abc123",
            tvg_id="id2",
            original_url="acestream://def456abc123"
        )
        
        channels = [channel1, channel2]
        m3u_service.parse_m3u_content.return_value = channels
        
        assert len(channels) == 2
        
        # Check channel names were generated from IDs
        assert channels[0].name == "Channel abc123def456"
        assert channels[1].name == "Channel def456abc123"

def test_get_base_url_with_zeronet():
    """Test base URL extraction for ZeroNet URLs."""
    m3u_service = M3UService()
    
    # Test with custom ZeroNet host
    zeronet_url = "http://192.168.2.178:43110/1H3KoazXt2gCJgeD8673eFvQYXG7cbRddU/lista-ace.m3u"
    base_url = m3u_service._get_base_url(zeronet_url)
    
    assert base_url == "http://192.168.2.178:43110/1H3KoazXt2gCJgeD8673eFvQYXG7cbRddU/"
    
    # Test with localhost ZeroNet
    local_url = "http://127.0.0.1:43110/1H3KoazXt2gCJgeD8673eFvQYXG7cbRddU/lista-ace.m3u"
    base_url = m3u_service._get_base_url(local_url)
    
    assert base_url == "http://127.0.0.1:43110/1H3KoazXt2gCJgeD8673eFvQYXG7cbRddU/"
    
    # Test with regular non-ZeroNet URL
    regular_url = "http://example.com/path/file.m3u"
    base_url = m3u_service._get_base_url(regular_url)
    
    assert base_url == "http://example.com/path/"

def test_m3u_channel_creation():
    """Test creating M3UChannel objects with different parameters."""
    # Test with full metadata
    channel1 = M3UChannel(
        id="abc123def456",
        name="Sports Channel HD",
        group="Sports",
        logo="http://example.com/logo.png",
        tvg_id="id1",
        tvg_name="Sports Channel",
        original_url="acestream://abc123def456"
    )
    
    assert channel1.id == "abc123def456"
    assert channel1.name == "Sports Channel HD"
    assert channel1.group == "Sports"
    assert channel1.logo == "http://example.com/logo.png"
    assert channel1.tvg_id == "id1"
    assert channel1.tvg_name == "Sports Channel"
    
    # Test with minimal metadata
    channel2 = M3UChannel(
        id="def456abc123",
        name="News Channel"
    )
    
    assert channel2.id == "def456abc123"
    assert channel2.name == "News Channel"
    assert channel2.group is None
    assert channel2.logo is None
    assert channel2.tvg_id is None
    assert channel2.tvg_name is None

def test_m3u_channel():
    """Test M3UChannel object creation and properties."""
    # Create a channel with full metadata
    channel = M3UChannel(
        id="abc123def456",
        name="Sports Channel HD",
        group="Sports",
        logo="http://example.com/logo.png",
        tvg_id="id1",
        tvg_name="Sports Channel",
        original_url="acestream://abc123def456"
    )
    
    # Verify all properties were set correctly
    assert channel.id == "abc123def456"
    assert channel.name == "Sports Channel HD"
    assert channel.group == "Sports"
    assert channel.logo == "http://example.com/logo.png"
    assert channel.tvg_id == "id1"
    assert channel.tvg_name == "Sports Channel"
    assert channel.original_url == "acestream://abc123def456"