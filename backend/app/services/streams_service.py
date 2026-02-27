import requests
from typing import Optional, Dict

class StreamsService:
    def __init__(self, acexy_url: Optional[str] = None, acestream_url: Optional[str] = None):
        self.acexy_url = acexy_url or "http://localhost:8001/api/streams/active"
        self.acestream_url = acestream_url or "http://localhost:6878/engine/active_streams"

    def get_active_streams_count(self) -> Dict:
        # Try acexy first
        try:
            resp = requests.get(self.acexy_url, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                return {"count": data.get("count", 0), "source": "acexy"}
        except Exception:
            pass
        # Fallback to acestream
        try:
            resp = requests.get(self.acestream_url, timeout=2)
            if resp.status_code == 200:
                data = resp.json() if resp.headers.get('content-type') == 'application/json' else {}
                count = data.get("count")
                if count is None:
                    # Try to parse from text if possible
                    count = int(resp.text.strip()) if resp.text.strip().isdigit() else 0
                return {"count": count, "source": "acestream"}
        except Exception:
            pass
        # If all fail
        return {"count": 0, "source": None, "error": "No stream source available"}
