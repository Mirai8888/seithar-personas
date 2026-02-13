#!/bin/bash
# Launch one or all personas
# Usage:
#   ./launch.sh rin              # launch rin only
#   ./launch.sh all              # launch all personas
#   ./launch.sh stop             # stop all personas
#   ./launch.sh status           # check who's running

ENGINE="$(dirname "$0")/engine.py"
PERSONAS_DIR="$(dirname "$0")"
LOG_DIR="/tmp/persona-logs"
mkdir -p "$LOG_DIR"

case "${1:-status}" in
    stop)
        pkill -f "engine.py --persona" 2>/dev/null
        echo "All personas stopped."
        ;;
    stopone)
        name="$2"
        pkill -f "engine.py --persona $name" 2>/dev/null
        echo "[$name] stopped."
        ;;
    status)
        echo "Running personas:"
        pgrep -af "engine.py --persona" || echo "  (none)"
        ;;
    all)
        for dir in "$PERSONAS_DIR"/*/; do
            name=$(basename "$dir")
            if [ -f "$dir/persona.json" ]; then
                # Kill existing
                pkill -f "engine.py --persona $name" 2>/dev/null
                sleep 0.5
                # Launch
                nohup python3 "$ENGINE" --persona "$name" > "$LOG_DIR/$name.log" 2>&1 &
                echo "[$name] launched (PID: $!)"
            fi
        done
        ;;
    *)
        name="$1"
        if [ -f "$PERSONAS_DIR/$name/persona.json" ]; then
            pkill -f "engine.py --persona $name\b" 2>/dev/null
            sleep 0.5
            nohup python3 "$ENGINE" --persona "$name" > "$LOG_DIR/$name.log" 2>&1 &
            echo "[$name] launched (PID: $!)"
        else
            echo "No persona.json found for '$name'"
            exit 1
        fi
        ;;
esac
