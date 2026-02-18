#!/usr/bin/env bash
# Start rin's full engagement loop (tweets every 2-6h, DM outreach every 4h).
# Groq first, local (Ollama) fallback. Set RIN_LOG for log path.

set -e
cd "$(dirname "$0")"
RIN_LOG="${RIN_LOG:-/tmp/rin-tweet.log}"
echo "[rin] Starting engagement loop. Log: $RIN_LOG"
nohup python3 -u tweet.py --loop >> "$RIN_LOG" 2>&1 &
echo $! > /tmp/rin-tweet.pid
echo "[rin] PID $(cat /tmp/rin-tweet.pid). To stop: kill \$(cat /tmp/rin-tweet.pid)"
