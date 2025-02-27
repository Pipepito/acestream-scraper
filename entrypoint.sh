#!/bin/sh

# Run database migrations
cd /app
echo "Running database migrations..."
python manage.py upgrade

# Setup ZeroNet config if not exists
ZERONET_CONFIG="/app/config/zeronet.conf"
if [ ! -f "$ZERONET_CONFIG" ]; then
    echo "Creating default ZeroNet config..."
    cat > "$ZERONET_CONFIG" << EOF
[global]
ui_ip = *
ui_host =
 0.0.0.0
 localhost
ui_port = 43110
EOF
fi

# Create symlink to config
ln -sf "$ZERONET_CONFIG" /app/ZeroNet/zeronet.conf

# Start ZeroNet in the background
cd /app/ZeroNet
echo "Starting ZeroNet..."
python3 zeronet.py main &
ZERONET_PID=$!

# Wait for ZeroNet to start
echo "Waiting for ZeroNet to initialize..."
sleep 10

# Start Flask app with Gunicorn with increased timeouts
cd /app
echo "Starting Flask application..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 300 \
    --keep-alive 5 \
    --worker-class uvicorn.workers.UvicornWorker \
    --log-level info \
    "wsgi:asgi_app"

# Monitor processes
echo "Services started. Monitoring processes..."
trap "kill $ZERONET_PID" EXIT