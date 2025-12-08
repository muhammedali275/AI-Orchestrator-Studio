#!/bin/bash

# Start AIpanel
echo "Starting AIpanel..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python -m app.db.session

# Start server
echo "Starting server..."
python -m app.main

# Deactivate virtual environment on exit
deactivate
