#!/bin/bash

# Exit on error
set -e

# Start the backend FastAPI app using uvicorn in background
echo "Starting backend at http://localhost:8000"
uvicorn app:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start the frontend Vite dev server in background
echo "Starting frontend at http://localhost:5173"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Run the interpreter with example pipeline (optional, runs once)
echo "Running pipeline interpreter with example pipeline..."
python3 engine/interpreter.py ast/example_pipeline.json

echo "Press Ctrl+C to stop servers."

# Wait for background processes to finish or be interrupted
wait $BACKEND_PID $FRONTEND_PID
