#!/bin/bash

# Simple wrapper to use the universal starter script.
# This avoids depending on gnome-terminal and works on headless servers.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/start-all-universal.sh"

