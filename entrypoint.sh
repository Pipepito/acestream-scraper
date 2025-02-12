#!/bin/sh

# Start ZeroNet in the background with the correct options
cd /app/ZeroNet
python3 zeronet.py --ui-ip '*' --ui-host '0.0.0.0' --ui-port 43110 main &
ZERONET_PID=$!

# Wait for ZeroNet to start
echo "Waiting for ZeroNet to start..."
sleep 10

# Start the Flask application with Gunicorn
cd /app
exec gunicorn --bind 0.0.0.0:8000 --workers 3 wsgi:app &
GUNICORN_PID=$!

# Monitor both processes
trap "kill $ZERONET_PID $GUNICORN_PID" EXIT
wait