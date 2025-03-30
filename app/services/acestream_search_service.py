import logging
import requests
import json
from typing import Dict, Any, List, Optional, Tuple

from app.extensions import db
from app.utils.config import Config

logger = logging.getLogger(__name__)

class AcestreamSearchService:
    """Service for searching Acestream channels via the engine API."""
    
    def __init__(self, engine_url: str = None):
        """Initialize search service with engine URL."""
        # Use provided URL or fetch from config
        if engine_url:
            self.engine_url = engine_url
        else:
            config = Config()
            # Fix: directly access the ace_engine_url property instead of calling get_config()
            self.engine_url = config.ace_engine_url
        
        # If URL doesn't start with a protocol, assume http://
        if not self.engine_url.startswith('http'):
            self.engine_url = f"http://{self.engine_url}"
        
        # Ensure the URL doesn't end with a slash
        self.engine_url = self.engine_url.rstrip('/')
        
        logger.debug(f"Acestream Search Service initialized with engine URL: {self.engine_url}")
    
    def search(self, query: str = "", page: int = 1, page_size: int = 10, category: str = "") -> Dict[str, Any]:
        """
        Search for Acestream channels using the engine API.
        
        Args:
            query: The search query string (optional, defaults to empty string for all channels)
            page: Page number for pagination (1-based)
            page_size: Number of results per page
            category: Filter by category (optional)
            
        Returns:
            Dict containing search results, pagination info, and status
        """
        try:
            # Construct search URL
            search_url = f"{self.engine_url}/search"
            
            # Convert from 1-based pagination (UI) to 0-based pagination (API)
            api_page = page - 1
            
            # Prepare query parameters
            params = {
                'query': query,
                'page': api_page,  # Send 0-based page index to the API
                'page_size': page_size
            }
            
            # Add category parameter if provided
            if category:
                params['category'] = category
            
            # Make request to Acestream engine
            logger.debug(f"Searching Acestream with query: '{query}' (empty query will return all channels), UI page: {page}, API page: {api_page}, page_size: {page_size}, category: {category}")
            logger.debug(f"Full search URL: {search_url}?query={query}&page={api_page}&page_size={page_size}" + (f"&category={category}" if category else ""))
            
            response = requests.get(search_url, params=params, timeout=10)
            
            # Enhanced logging - log the actual status code
            logger.info(f"Search API response status code: {response.status_code}")
            
            # Check if request was successful
            if response.status_code == 200:
                # Log the raw API response for debugging
                raw_response = response.text
                logger.debug(f"Raw API response: {raw_response[:1000]}..." if len(raw_response) > 1000 else raw_response)
                
                try:
                    search_data = response.json()
                    
                    # Log the parsed JSON structure
                    logger.debug(f"Parsed JSON response: {json.dumps(search_data)[:1000]}..." if len(json.dumps(search_data)) > 1000 else json.dumps(search_data))
                    
                    # Log if 'result' key exists in the response
                    if 'result' in search_data:
                        logger.debug("'result' key found in API response")
                    else:
                        logger.warning("'result' key NOT found in API response")
                        logger.debug(f"Available keys in response: {list(search_data.keys())}")
                    
                    # Handle the nested structure from Acestream API
                    # The API response has a 'result' key containing the actual data
                    api_result = search_data.get('result', {})
                    
                    # Check if we got a valid result dictionary
                    if not api_result and 'result' in search_data:
                        logger.warning("Empty 'result' dictionary received from API")
                    
                    # Extract data from the nested structure
                    raw_results = api_result.get('results', [])
                    total_results = api_result.get('total', 0)
                    
                    # Transform the results to have a proper ID field
                    # Each result might have 'items' which contain the infohash
                    processed_results = []
                    
                    for result in raw_results:
                        # Handle the expected structure with 'name' and 'items'
                        if 'items' in result and isinstance(result['items'], list) and len(result['items']) > 0:
                            for item in result['items']:
                                # Create a processed result with the required fields
                                processed_item = {
                                    'name': result.get('name', 'Unnamed Channel'),
                                    'id': item.get('infohash', ''), # Use the infohash as ID
                                    'categories': item.get('categories', []),
                                    'bitrate': item.get('bitrate', 0)
                                }
                                # Add any other useful fields from the item
                                for key, value in item.items():
                                    if key not in processed_item and key != 'infohash':
                                        processed_item[key] = value
                                
                                processed_results.append(processed_item)
                        else:
                            # If the expected structure is not present, log it and try to use the result directly
                            logger.warning(f"Unexpected result structure without 'items': {result}")
                            # Try to extract an ID from the result if possible
                            result_id = result.get('infohash', result.get('id', ''))
                            if result_id:
                                result['id'] = result_id
                                processed_results.append(result)
                    
                    # Log the number of results found
                    logger.debug(f"Extracted {len(processed_results)} processed results from API response")
                    logger.debug(f"Total results reported by API: {total_results}")
                    
                    # Process and structure the response
                    result = {
                        'success': True,
                        'message': 'Search successful',
                        'results': processed_results,
                        'pagination': {
                            'page': page,  # Return the original 1-based page for the UI
                            'page_size': page_size,
                            'total_results': total_results,
                            'total_pages': (total_results + page_size - 1) // page_size if total_results > 0 else 0
                        }
                    }
                    
                    query_description = query if query else "all channels"
                    logger.info(f"Found {len(processed_results)} results for query '{query_description}'")
                    return result
                except json.JSONDecodeError as json_err:
                    logger.error(f"Failed to parse JSON response: {json_err}")
                    logger.error(f"Raw response content (first 500 chars): {response.text[:500]}")
                    return {
                        'success': False,
                        'message': f"Failed to parse API response: {json_err}",
                        'results': [],
                        'pagination': {
                            'page': page,
                            'page_size': page_size,
                            'total_results': 0,
                            'total_pages': 0
                        }
                    }
            else:
                error_msg = f"Acestream search failed with status code {response.status_code}"
                logger.error(error_msg)
                logger.error(f"Response content: {response.text[:500]}..." if len(response.text) > 500 else response.text)
                return {
                    'success': False,
                    'message': error_msg,
                    'results': [],
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_results': 0,
                        'total_pages': 0
                    }
                }
        except Exception as e:
            error_msg = f"Error searching Acestream: {str(e)}"
            logger.error(error_msg)
            # Log the exception details for debugging
            logger.exception("Exception details:")
            return {
                'success': False,
                'message': error_msg,
                'results': [],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_results': 0,
                    'total_pages': 0
                }
            }
    
    def extract_acestream_id(self, url: str) -> Optional[str]:
        """
        Extract acestream ID from a URL.
        
        Args:
            url: Acestream URL
            
        Returns:
            Extracted ID or None if not found
        """
        if url.startswith('acestream://'):
            return url.split('acestream://')[1]
        return None