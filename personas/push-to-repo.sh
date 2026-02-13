#!/usr/bin/env bash
# Clone repo to /tmp, copy our files in, commit and push.
# Run from workspace:  cd ~/.openclaw/workspace && bash personas/push-to-repo.sh
# (Git doesn't work from the openclaw workspace path, so we use a temp clone.)

set -e
WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
REPO_DIR="/tmp/seithar-personas"
REPO_URL="https://github.com/Mirai8888/seithar-personas.git"

if ! [ -d "$REPO_DIR/.git" ]; then
  echo "Cloning repo to $REPO_DIR ..."
  git clone "$REPO_URL" "$REPO_DIR"
fi

echo "Copying files from workspace into clone ..."
# Repo has engine.py, launch.sh at root; we have them under personas/
cp "$WORKSPACE/personas/engine.py" "$REPO_DIR/engine.py"
cp "$WORKSPACE/personas/launch.sh" "$REPO_DIR/launch.sh"
mkdir -p "$REPO_DIR/personas/rin"
cp "$WORKSPACE/personas/rin/tweet.py" "$REPO_DIR/personas/rin/"
cp "$WORKSPACE/personas/rin/bot.py" "$REPO_DIR/personas/rin/"
cp "$WORKSPACE/personas/rin/start-engagement-loop.sh" "$REPO_DIR/personas/rin/"
cp "$WORKSPACE/personas/start-all-local.sh" "$WORKSPACE/personas/start-rin.sh" "$REPO_DIR/personas/"
cp "$WORKSPACE/personas/push-to-repo.sh" "$REPO_DIR/personas/"

cd "$REPO_DIR"
git add -A
git status
if git diff --cached --quiet; then
  echo "Nothing to commit."
  exit 0
fi
git commit -m "rin: tweet loop robustness, DM every 10 min, safe Groq load"
git push origin main

echo "Pushed to $REPO_URL"
