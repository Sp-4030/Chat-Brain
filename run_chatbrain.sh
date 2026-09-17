#!/bin/bash

echo "========================================"
echo "          CHATBRAIN STARTING"
echo "========================================"
echo

cd "$(dirname "$0")" || exit 1

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python is not installed."
    exit 1
fi

echo "Python command: $PYTHON_CMD"
echo

echo "Starting YouTube ChatBrain..."
"$PYTHON_CMD" youtube.py &
YOUTUBE_PID=$!

sleep 5

echo "Starting Streamlit Dashboard..."
"$PYTHON_CMD" -m streamlit run app.py &
STREAMLIT_PID=$!

echo
echo "========================================"
echo "         CHATBRAIN STARTED"
echo "========================================"
echo
echo "YouTube ChatBrain PID : $YOUTUBE_PID"
echo "Streamlit Dashboard PID: $STREAMLIT_PID"
echo
echo "Dashboard: http://localhost:8501"
echo
echo "========================================"

cleanup() {
    echo
    echo "Stopping ChatBrain..."
    kill "$YOUTUBE_PID" 2>/dev/null
    kill "$STREAMLIT_PID" 2>/dev/null
    echo "ChatBrain stopped."
}

trap cleanup EXIT INT TERM

wait