#!/usr/bin/env bash
# Start rin's full engagement loop (tweets every 2-6h, DM outreach every 10 min).
# Run from repo root or: bash start-engagement-loop.sh
#
# Optional: prefer local Ollama over Groq (avoids rate limits):
#   RIN_USE_LOCAL_FIRST=1 nohup bash start-engagement-loop.sh &
#
# Requires: Ollama running with mistral (ollama serve; ollama pull mistral)
# Log: /tmp/rin-tweet.log (or set RIN_LOG path)

set -e
cd "$(dirname "$0")"
RIN_LOG="${RIN_LOG:-/tmp/rin-tweet.log}"
echo "[rin] Starting engagement loop. Log: $RIN_LOG"
nohup python3 -u tweet.py --loop >> "$RIN_LOG" 2>&1 &
echo $! > /tmp/rin-tweet.pid
echo "[rin] PID $(cat /tmp/rin-tweet.pid). To stop: kill \$(cat /tmp/rin-tweet.pid)"
