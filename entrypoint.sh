#!/bin/bash
set -e

# If the first argument is "pytest", run pytest instead of main.py
if [ "$1" = "pytest" ]; then
    exec pytest "${@:2}"
else
    # Run the Python script with arguments
    exec python /app/src/main.py "$@"
fi