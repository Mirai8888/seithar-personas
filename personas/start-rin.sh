#!/usr/bin/env bash
# Start Rin only, using local inference (Ollama) for Discord + tweets.
#
# Prereqs:
#   - Ollama running:  OLLAMA_GPU=1 ollama serve
#   - Model pulled:    ollama pull <model>   (e.g. llama3.2, mistral)
#
# Optional env (set before running to override):
#   PERSONA_LOCAL_MODEL=<name>   (default: mistral; use your pulled model, e.g. llama3.2)
#   PERSONA_LOCAL_TIMEOUT=45
#
# What this starts:
#   1. Rin Discord bot (engine.py --persona rin) — local inference only
#   2. Rin engagement loop (tweets + DMs) — local inference only
#
# Logs:
#   - Rin:   /tmp/persona-logs/rin.log
#   - Loop:  /tmp/rin-tweet.log
#
# Stop:
#   ./launch.sh stop
#   kill $(cat /tmp/rin-tweet.pid)

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Local-only: no Groq; Ollama for Discord and tweet/DM generation
export PERSONA_LOCAL_ONLY=1
export RIN_LOCAL_ONLY=1

echo "[personas] Rin only, local inference (PERSONA_LOCAL_MODEL=${PERSONA_LOCAL_MODEL:-mistral})..."

# Stop any other personas so only Rin runs
bash launch.sh stop 2>/dev/null || true

# 1. Rin Discord bot
bash launch.sh rin

# 2. Rin engagement loop
RIN_LOG="${RIN_LOG:-/tmp/rin-tweet.log}"
if [ -f rin/start-engagement-loop.sh ]; then
    bash rin/start-engagement-loop.sh
else
    nohup python3 -u rin/tweet.py --loop >> "$RIN_LOG" 2>&1 &
    echo $! > /tmp/rin-tweet.pid
    echo "[rin] Tweet loop PID $(cat /tmp/rin-tweet.pid). Log: $RIN_LOG"
fi

echo "[personas] Rin started. Discord: /tmp/persona-logs/rin.log | Loop: tail -f $RIN_LOG"
