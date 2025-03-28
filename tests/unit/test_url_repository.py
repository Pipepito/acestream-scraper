import pytest
import uuid
from app.repositories import URLRepository
from app.models import ScrapedURL

def test_url_repository_get_by_id(db_session):
    """Test that URLs can be retrieved by their UUID."""
    repo = URLRepository()
    
    # Create a URL with explicit ID and type
    test_id = str(uuid.uuid4())
    url = ScrapedURL(
        id=test_id,
        url="http://example.com/test",
        url_type="regular",
        status="pending"
    )
    db_session.add(url)
    db_session.commit()
    
    # Retrieve by ID
    retrieved = repo.get_by_id(test_id)
    assert retrieved is not None
    assert retrieved.id == test_id
    assert retrieved.url == "http://example.com/test"
    assert retrieved.url_type == "regular"

def test_url_repository_add_with_type(db_session):
    """Test adding a URL with explicit type."""
    repo = URLRepository()
    
    # Add a regular URL
    url_obj1 = repo.add("http://example.com/regular", "regular")
    assert url_obj1.url_type == "regular"
    
    # Add a zeronet URL
    url_obj2 = repo.add("zero://example", "zeronet")
    assert url_obj2.url_type == "zeronet"
    
    # Verify they were added with different IDs
    assert url_obj1.id != url_obj2.id
    assert isinstance(url_obj1.id, str)
    assert isinstance(url_obj2.id, str)
    
    # Verify they can be retrieved
    assert repo.get_by_url("http://example.com/regular") is not None
    assert repo.get_by_url("zero://example") is not None

def test_url_repository_delete_by_id(db_session):
    """Test deleting a URL by ID."""
    repo = URLRepository()
    
    # Add a URL
    url_obj = repo.add("http://example.com/delete", "regular")
    url_id = url_obj.id
    
    # Verify it exists
    assert repo.get_by_id(url_id) is not None
    
    # Delete by ID
    result = repo.delete(url_id)
    assert result is True
    
    # Verify it's gone
    assert repo.get_by_id(url_id) is None

def test_url_repository_update_url_type(db_session):
    """Test updating a URL's type."""
    repo = URLRepository()
    
    # Add a URL
    url = "http://example.com/update-type"
    url_obj = repo.add(url, "regular")
    
    # Update type
    updated = repo.update_url_type(url, "zeronet")
    
    # Verify type was updated
    assert updated is not None
    assert updated.url_type == "zeronet"
    
    # Verify retrieving it shows the updated type
    retrieved = repo.get_by_url(url)
    assert retrieved.url_type == "zeronet"
