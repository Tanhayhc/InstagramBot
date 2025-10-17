#!/bin/bash

echo "Starting Instagram Automation Bot..."

python server.py &
SERVER_PID=$!
echo "Flask server started (PID: $SERVER_PID)"

python main.py &
BOT_PID=$!
echo "Instagram bot started (PID: $BOT_PID)"

wait
