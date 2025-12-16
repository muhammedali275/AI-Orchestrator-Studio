#!/bin/bash
echo "Starting ZainOne Orchestrator Studio Frontend..."

# Inject app version into env from root package.json
if [[ -f package.json ]]; then
	VERSION=$(node -e "console.log(require('./package.json').version || 'dev')" 2>/dev/null)
	if [[ -z "$VERSION" ]]; then VERSION="dev"; fi
	export REACT_APP_VERSION="$VERSION"
	echo "Detected version: $REACT_APP_VERSION"
else
	export REACT_APP_VERSION="dev"
	echo "package.json not found at repo root, using version: $REACT_APP_VERSION"
fi

cd frontend
npm start
