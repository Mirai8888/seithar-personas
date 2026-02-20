#!/usr/bin/env bash
# Start all persona components using local inference (Ollama).
#
# Prereqs:
#   - Ollama running:  ollama serve
#   - Model pulled:    ollama pull mistral
#
# Optional env (set before running if you want to override):
#   PERSONA_LOCAL_MODEL=mistral   (default; use any Ollama model name)
#
# What this starts:
#   1. All Discord personas (rin, kei, nomi, glass, sable, sorath) via engine.py
#      - They use Ollama for replies when PERSONA_USE_LOCAL=1
#   2. Rin's engagement loop (tweets every 2-6h, DM outreach every 10 min)
#      - Uses Ollama for tweet/DM generation when RIN_USE_LOCAL_FIRST=1
#
# Logs:
#   - Personas: /tmp/persona-logs/<name>.log
#   - Rin loop: /tmp/rin-tweet.log
#   - PIDs:     /tmp/rin-tweet.pid (rin loop only; personas see launch.sh)
#
# Stop:
#   ./launch.sh stop          # stop all Discord personas
#   kill $(cat /tmp/rin-tweet.pid)  # stop rin tweet loop

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Groq is used first; Ollama/vLLM is fallback when Groq fails.
# To force local-only (no Groq): export PERSONA_LOCAL_ONLY=1 RIN_LOCAL_ONLY=1 before running.

echo "[personas] Starting all components (Groq first, local fallback)..."

# 1. All Discord personas (engine.py per persona)
bash launch.sh all

# 2. Rin engagement loop (tweets + DMs)
RIN_LOG="${RIN_LOG:-/tmp/rin-tweet.log}"
if [ -f rin/start-engagement-loop.sh ]; then
    bash rin/start-engagement-loop.sh
else
    nohup python3 -u rin/tweet.py --loop >> "$RIN_LOG" 2>&1 &
    echo $! > /tmp/rin-tweet.pid
    echo "[rin] Tweet loop PID $(cat /tmp/rin-tweet.pid). Log: $RIN_LOG"
fi

echo "[personas] All started. Persona logs: /tmp/persona-logs/<name>.log"
echo "[personas] Rin loop: tail -f /tmp/rin-tweet.log"
