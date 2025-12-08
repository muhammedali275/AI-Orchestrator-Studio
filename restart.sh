#!/bin/bash
echo "========================================"
echo "Restarting ZainOne Orchestrator Studio"
echo "========================================"
echo ""

# First stop all services
echo "Stopping all services..."
./stop-all.sh

echo ""
echo "Waiting 3 seconds before starting services again..."
sleep 3
echo ""

# Then start all services
echo "Starting all services..."
./start-all-universal.sh

echo ""
echo "========================================"
echo "Restart complete!"
echo "========================================"
