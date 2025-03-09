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

# Start Tor if enabled
if [ "$ENABLE_TOR" = "true" ]; then
    echo "Starting Tor service..."
    service tor start
    # Add a brief pause to ensure Tor has time to start
    sleep 3
fi

# Start Acexy if enabled
if [ "$ENABLE_ACEXY" = "true" ]; then
    echo "Starting Acestream engine and Acexy proxy..."
    
    if [[ $ALLOW_REMOTE_ACCESS == "yes" ]];then
        EXTRA_FLAGS="$EXTRA_FLAGS --bind-all"
    fi
    # Start the Acestream engine
    /opt/acestream/start-engine --client-console --http-port $ACESTREAM_HTTP_PORT $EXTRA_FLAGS &
    
    # Brief pause to allow Acestream engine to start
    sleep 3
    
    # Start Acexy proxy
    /usr/local/bin/acexy &
fi

# Start ZeroNet in the background
cd /app/ZeroNet
echo "Starting ZeroNet..."
python3 zeronet.py main &
ZERONET_PID=$!

# Wait for ZeroNet to start
echo "Waiting for ZeroNet to initialize..."
sleep 10

# Start Flask app with Gunicorn
cd /app
echo "Starting Flask application..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 300 \
    --keep-alive 5 \
    --worker-class uvicorn.workers.UvicornWorker \
    --log-level info \
    "wsgi:asgi_app" &
GUNICORN_PID=$!

# Monitor processes
echo "Services started. Monitoring processes..."
trap "echo 'Shutting down services...'; kill $(jobs -p)" EXIT INT TERM QUIT

# Wait for any process to exit
wait