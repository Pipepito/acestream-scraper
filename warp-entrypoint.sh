#!/bin/bash
# filepath: f:\Projects\acestream-scraper\warp-entrypoint.sh

# Initialize WARP first
/app/warp-setup.sh

# Now run the original entrypoint
exec /app/entrypoint.sh "$@"