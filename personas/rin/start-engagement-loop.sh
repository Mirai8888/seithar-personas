#!/usr/bin/env bash
# Start rin's engagement: tweets every 2-6h, send DMs from DB every 10 min (LLM).
# Scraper (no LLM) fills the DMable DB; run it in background for continuous crawl.
#
# Optional: start scraper in background (builds DB while loop runs):
#   RIN_START_SCRAPER=1 bash start-engagement-loop.sh
#
# Optional: prefer local Ollama over Groq:
#   RIN_USE_LOCAL_FIRST=1 nohup bash start-engagement-loop.sh &
#
# Log: /tmp/rin-tweet.log (loop), /tmp/rin-scraper.log (scraper)

set -e
cd "$(dirname "$0")"
RIN_LOG="${RIN_LOG:-/tmp/rin-tweet.log}"
RIN_SCRAPER_LOG="${RIN_SCRAPER_LOG:-/tmp/rin-scraper.log}"

if [ -n "${RIN_START_SCRAPER:-}" ]; then
  echo "[rin] Starting scraper in background. Log: $RIN_SCRAPER_LOG"
  nohup python3 -u tweet.py --scraper >> "$RIN_SCRAPER_LOG" 2>&1 &
  echo $! > /tmp/rin-scraper.pid
  echo "[rin] Scraper PID $(cat /tmp/rin-scraper.pid). To stop: kill \$(cat /tmp/rin-scraper.pid)"
fi

echo "[rin] Starting engagement loop. Log: $RIN_LOG"
nohup python3 -u tweet.py --loop >> "$RIN_LOG" 2>&1 &
echo $! > /tmp/rin-tweet.pid
echo "[rin] Loop PID $(cat /tmp/rin-tweet.pid). To stop: kill \$(cat /tmp/rin-tweet.pid)"
