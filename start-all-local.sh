#!/usr/bin/env bash
# Start all persona components. Groq first, Ollama/vLLM as fallback.
#
# Prereqs for local fallback: ollama serve; ollama pull mistral
# To force local-only: export PERSONA_LOCAL_ONLY=1 RIN_LOCAL_ONLY=1 before running.
#
# What this starts:
#   1. All Discord personas via engine.py (personas/*/persona.json)
#   2. Rin's engagement loop (rin/tweet.py --loop) if rin/ exists

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[personas] Starting all components (Groq first, local fallback)..."

bash launch.sh all

RIN_LOG="${RIN_LOG:-/tmp/rin-tweet.log}"
if [ -f rin/start-engagement-loop.sh ]; then
    bash rin/start-engagement-loop.sh
elif [ -f rin/tweet.py ]; then
    nohup python3 -u rin/tweet.py --loop >> "$RIN_LOG" 2>&1 &
    echo $! > /tmp/rin-tweet.pid
    echo "[rin] Tweet loop PID $(cat /tmp/rin-tweet.pid). Log: $RIN_LOG"
fi

echo "[personas] All started. Persona logs: /tmp/persona-logs/<name>.log"
echo "[personas] Rin loop: tail -f /tmp/rin-tweet.log"
