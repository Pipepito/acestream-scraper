#!/bin/bash

# Create logs directory
LOG_DIR="/app/logs"
mkdir -p $LOG_DIR

# Configure log rotation - hourly rotation, keep 1 day of logs
cat > /etc/logrotate.d/acestream-services << EOF
$LOG_DIR/*.log {
    hourly
    rotate 7
    compress
    missingok
    notifempty
    create 0644 root root
}
EOF

# Run logrotate once to ensure config is valid
logrotate /etc/logrotate.d/acestream-services --debug

# Initialize WARP if enabled
if [ "${ENABLE_WARP}" = "true" ]; then
    echo "Initializing Cloudflare WARP..."
    /app/warp-setup.sh
fi

# Set ENABLE_ACESTREAM_ENGINE to match ENABLE_ACEXY if not explicitly set
if [ -z "${ENABLE_ACESTREAM_ENGINE+x}" ]; then
    export ENABLE_ACESTREAM_ENGINE=$ENABLE_ACEXY
    echo "ENABLE_ACESTREAM_ENGINE not set, using ENABLE_ACEXY value: $ENABLE_ACESTREAM_ENGINE"
fi
# Update ACESTREAM_HTTP_HOST to use the actual value of ACEXY_HOST
if [ "$ACESTREAM_HTTP_HOST" = "ACEXY_HOST" ]; then
    export ACESTREAM_HTTP_HOST="$ACEXY_HOST"
    echo "Setting ACESTREAM_HTTP_HOST to $ACEXY_HOST"
fi
# Note: Database migrations are now automatically handled in the Flask app startup
# rather than in this script, preventing duplication of migration execution

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
    service tor start >> "$LOG_DIR/tor.log" 2>&1
    # Add a brief pause to ensure Tor has time to start
    sleep 3
    echo "Tor service logs available at $LOG_DIR/tor.log"
fi

# Start Acestream Engine if enabled
if [ "$ENABLE_ACESTREAM_ENGINE" = "true" ]; then
    echo "Starting Acestream engine..."
    if [ "$ALLOW_REMOTE_ACCESS" = "yes" ]; then
        EXTRA_FLAGS="$EXTRA_FLAGS --bind-all"
    fi
    /opt/acestream/start-engine --client-console --http-port $ACESTREAM_HTTP_PORT $EXTRA_FLAGS >> "$LOG_DIR/acestream.log" 2>&1 &  
    sleep 3 # Brief pause to allow Acestream engine to start
    echo "Acestream engine logs available at $LOG_DIR/acestream.log"
fi

# Start Acexy if enabled
if [ "$ENABLE_ACEXY" = "true" ]; then
    if [ "$ENABLE_ACESTREAM_ENGINE" = "false" ] && [ "$ACEXY_HOST" = "localhost" ] && [ "$ACEXY_PORT" = "6878" ]; then
        echo "ERROR: When Acestream Engine is disabled, you must specify ACEXY_HOST and ACEXY_PORT other than localhost to connect to an external Acestream Engine instance"
        exit 1
    fi
    
    echo "Starting Acexy proxy..."
    export ACEXY_HOST
    export ACEXY_PORT
    /usr/local/bin/acexy >> "$LOG_DIR/acexy.log" 2>&1 &
    echo "Acexy proxy logs available at $LOG_DIR/acexy.log"
else
    echo "Acexy is disabled."
fi

# Start ZeroNet in the background
cd /app/ZeroNet
echo "Starting ZeroNet..."
python3 zeronet.py main >> "$LOG_DIR/zeronet.log" 2>&1 &
ZERONET_PID=$!
echo "ZeroNet logs available at $LOG_DIR/zeronet.log"

# Wait for ZeroNet to start
echo "Waiting for ZeroNet to initialize..."
sleep 10

# Start Flask app with Gunicorn
cd /app
echo "Starting Flask application on port $FLASK_PORT..."
exec gunicorn \
    --bind "0.0.0.0:$FLASK_PORT" \
    --workers 3 \
    --timeout 300 \
    --keep-alive 5 \
    --worker-class uvicorn.workers.UvicornWorker \
    --log-level info \
    --access-logfile "$LOG_DIR/gunicorn-access.log" \
    --error-logfile "$LOG_DIR/gunicorn-error.log" \
    "wsgi:asgi_app" &
GUNICORN_PID=$!
echo "Flask application logs available at $LOG_DIR/gunicorn-access.log and $LOG_DIR/gunicorn-error.log"

# Monitor processes
echo "Services started. Monitoring processes..."
trap "echo 'Shutting down services...'; kill $(jobs -p)" EXIT INT TERM QUIT

# Wait for any process to exit
wait
