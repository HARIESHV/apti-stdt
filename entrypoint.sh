#!/bin/sh
set -e

echo "Starting AptitudePro Entrypoint Script..."

# Default MONGO_URI if not set
if [ -z "$MONGO_URI" ]; then
  export MONGO_URI="mongodb://localhost:27017/aptipro"
  echo "WARNING: MONGO_URI not set. Defaulting to $MONGO_URI"
fi

# Run the application
python app.py
