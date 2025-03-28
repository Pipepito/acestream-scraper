import pytest
import uuid
from app.repositories import ChannelRepository, URLRepository
from app.models import AcestreamChannel, ScrapedURL

def test_filter_channels_by_source_url(db_session):
    """Test filtering channels by source URL."""
    channel_repo = ChannelRepository()
    url_repo = URLRepository()
    
    # Create two URLs with different IDs
    url1 = ScrapedURL(
        id=str(uuid.uuid4()),
        url="http://example.com/source1",
        url_type="regular"
    )
    url2 = ScrapedURL(
        id=str(uuid.uuid4()),
        url="http://example.com/source2",
        url_type="regular"
    )
    db_session.add_all([url1, url2])
    db_session.commit()
    
    # Create channels for each URL
    channels1 = [
        AcestreamChannel(id=f"id1_{i}", name=f"Channel 1-{i}", source_url=url1.url)
        for i in range(3)
    ]
    channels2 = [
        AcestreamChannel(id=f"id2_{i}", name=f"Channel 2-{i}", source_url=url2.url)
        for i in range(2)
    ]
    db_session.add_all(channels1 + channels2)
    db_session.commit()
    
    # Test filtering by source URL
    channels_for_url1 = channel_repo.get_by_source(url1.url)
    assert len(channels_for_url1) == 3
    for ch in channels_for_url1:
        assert ch.source_url == url1.url
        assert ch.name.startswith("Channel 1-")
    
    channels_for_url2 = channel_repo.get_by_source(url2.url)
    assert len(channels_for_url2) == 2
    for ch in channels_for_url2:
        assert ch.source_url == url2.url
        assert ch.name.startswith("Channel 2-")

# This test needs to be updated to avoid using the client directly
# Instead, let's test the repository methods directly
def test_get_channels_by_url_id(db_session):
    """Test getting channels by URL ID using the repository."""
    # Create URLs and channels in the database
    url1 = ScrapedURL(
        id=str(uuid.uuid4()),
        url="http://example.com/sourceA",
        url_type="regular"
    )
    url2 = ScrapedURL(
        id=str(uuid.uuid4()),
        url="http://example.com/sourceB",
        url_type="regular"
    )
    db_session.add_all([url1, url2])
    db_session.commit()
    
    # Add channels for each URL
    channels1 = [
        AcestreamChannel(id=f"idA_{i}", name=f"Channel A-{i}", source_url=url1.url)
        for i in range(3)
    ]
    channels2 = [
        AcestreamChannel(id=f"idB_{i}", name=f"Channel B-{i}", source_url=url2.url)
        for i in range(2)
    ]
    db_session.add_all(channels1 + channels2)
    db_session.commit()
    
    # Initialize repositories
    channel_repo = ChannelRepository()
    url_repo = URLRepository()
    
    # Test URL 1
    url1_obj = url_repo.get_by_id(url1.id)
    assert url1_obj is not None
    
    channels_for_url1 = channel_repo.get_by_source(url1_obj.url)
    assert len(channels_for_url1) == 3
    channel_names = [ch.name for ch in channels_for_url1]
    for i in range(3):
        assert f"Channel A-{i}" in channel_names
    
    # Test URL 2
    url2_obj = url_repo.get_by_id(url2.id)
    assert url2_obj is not None
    
    channels_for_url2 = channel_repo.get_by_source(url2_obj.url)
    assert len(channels_for_url2) == 2
    channel_names = [ch.name for ch in channels_for_url2]
    for i in range(2):
        assert f"Channel B-{i}" in channel_names
    
    # Test non-existent URL ID
    non_existent_id = str(uuid.uuid4())
    non_existent_url = url_repo.get_by_id(non_existent_id)
    assert non_existent_url is None
