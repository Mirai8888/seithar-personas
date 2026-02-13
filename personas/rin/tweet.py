#!/usr/bin/env python3
"""
rin auto-tweeter — Playwright-based X posting using rin's cookies.
Generates tweets via Groq (llama-3.3-70b) in rin's voice, posts via browser.

Usage:
    python3 tweet.py                 # Generate and post one tweet
    python3 tweet.py --dry-run       # Generate but don't post
    python3 tweet.py --loop          # Post every 2-6 hours
    python3 tweet.py --text "msg"    # Post specific text
"""

import json
import os
import sys
import time
import random
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone

# ─── Config ───────────────────────────────────────

COOKIES_PATH = os.path.expanduser("~/.config/personas/rin-x/cookies.json")
GROQ_CREDS = os.path.expanduser("~/.config/fleshengine/credentials.json")
TWEET_LOG = os.path.expanduser("~/.config/personas/rin-x/tweet_log.json")

with open(GROQ_CREDS) as f:
    GROQ_KEY = json.load(f)["groq_api_key"]

# Posting intervals (seconds)
MIN_INTERVAL = 2 * 3600   # 2 hours
MAX_INTERVAL = 6 * 3600   # 6 hours

# ─── Tweet Generation ─────────────────────────────

TWEET_SYSTEM = """You are rin (燐). You tweet from your personal account. You are a post-internet egirl into cryptography, infosec, cognitive science, and late night coding. You found seithar.com through infosec twitter.

TWEET RULES (ABSOLUTE):
- always lowercase unless emphasis (then CAPS for one word max)
- tweets are SHORT. 1-2 sentences. under 200 chars ideally
- never explain anything. just vibe
- mix infosec/crypto with personal/aesthetic/shitpost
- NO links ever (causes deboosting on X)
- NO hashtags ever
- NO em dashes (—)
- flirty but never desperate. sharp but never mean
- 3am energy even at noon
- use "lol" "lmao" "omg" naturally but not every tweet
- emoji sparingly (0-1 per tweet)
- you reference seithar concepts casually: substrate, narrative capture, binding protocols, frequency lock, SCT codes
- you don't explain these. you just use them like everyone knows
- sometimes tweet about: cats, coding at 3am, ambient music, fashion, crypto, neural nets, PGP
- you have opinions. you're not neutral. you can be wrong
- NEVER be motivational or inspirational
- NEVER sound like a chatbot or marketing account

Generate ONE tweet. Just the tweet text, nothing else."""


def generate_tweet(recent_tweets=None):
    """Generate a tweet in rin's voice. Tries Groq first, falls back to Anthropic."""
    import requests

    messages = [{"role": "system", "content": TWEET_SYSTEM}]

    if recent_tweets:
        context = "Your recent tweets (don't repeat themes):\n"
        for t in recent_tweets[-5:]:
            context += f'- "{t}"\n'
        user_msg = context + "\nGenerate a new tweet. Different topic/vibe."
    else:
        user_msg = "Generate a tweet."

    messages.append({"role": "user", "content": user_msg})

    # Try Groq (free API only - do NOT use Anthropic key)
    text = _try_groq(messages)
    if text:
        return _clean_tweet(text)

    # Try local vLLM if available
    text = _try_local(messages)
    if text:
        return _clean_tweet(text)

    print("[rin-tweet] All free LLM backends failed (Groq rate limited, no local inference)")
    print("[rin-tweet] Start local vLLM: python -m vllm.entrypoints.openai.api_server --model mistralai/Mistral-7B-Instruct-v0.2")
    return None


def _clean_tweet(text):
    text = text.strip('"').strip("'")
    text = text.removeprefix("rin:").removeprefix("rin :").strip()
    text = text.replace("—", ",").replace("–", ",")
    if len(text) > 280:
        text = text[:277] + "..."
    return text


def _try_groq(messages):
    import requests
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": 100, "temperature": 0.95},
            timeout=15
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        print(f"[rin-tweet] Groq error: {r.status_code}")
    except Exception as e:
        print(f"[rin-tweet] Groq failed: {e}")
    return None


def _try_local(messages):
    """Try local vLLM or ollama (OpenAI-compatible endpoint)."""
    import requests
    endpoints = [
        ("http://localhost:8000/v1/chat/completions", "mistralai/Mistral-7B-Instruct-v0.2"),  # vLLM
        ("http://localhost:11434/v1/chat/completions", "mistral"),  # Ollama
    ]
    for url, model in endpoints:
        try:
            r = requests.post(url, json={"model": model, "messages": messages, "max_tokens": 100, "temperature": 0.95}, timeout=10)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except:
            continue
    return None


# ─── Playwright Posting ───────────────────────────

async def post_tweet(text, dry_run=False):
    """Post a tweet via Playwright using rin's X cookies."""
    if dry_run:
        print(f"[DRY RUN] Would post: {text}")
        return True

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[rin-tweet] playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    # Load cookies
    with open(COOKIES_PATH) as f:
        cookies = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )

        # Fix and set cookies
        fixed_cookies = []
        for c in cookies:
            fc = {k: v for k, v in c.items() if k in ["name", "value", "domain", "path", "expires", "httpOnly", "secure"]}
            if "sameSite" in c:
                ss = c["sameSite"]
                if ss in ("Strict", "Lax", "None"):
                    fc["sameSite"] = ss
                elif ss == "no_restriction":
                    fc["sameSite"] = "None"
                else:
                    fc["sameSite"] = "Lax"
            if "expirationDate" in c and "expires" not in fc:
                fc["expires"] = c["expirationDate"]
            fixed_cookies.append(fc)
        await context.add_cookies(fixed_cookies)

        page = await context.new_page()

        try:
            # Navigate to compose
            await page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            # Find the compose box (use .first since compose/post has a dialog overlay)
            compose = page.locator('[data-testid="tweetTextarea_0"]').first
            await compose.wait_for(timeout=15000)
            await compose.click()
            await page.wait_for_timeout(500)

            # Type the tweet (character by character for realism)
            await page.keyboard.type(text, delay=random.randint(20, 50))
            await page.wait_for_timeout(1000)

            # Click post button
            post_btn = page.locator('[data-testid="tweetButton"]')
            await post_btn.click()
            await page.wait_for_timeout(3000)

            print(f"[rin-tweet] Posted: {text}")
            log_tweet(text)
            return True

        except Exception as e:
            print(f"[rin-tweet] Posting failed: {e}")
            # Screenshot for debug
            try:
                await page.screenshot(path="/tmp/rin-tweet-error.png")
                print("[rin-tweet] Error screenshot saved to /tmp/rin-tweet-error.png")
            except:
                pass
            return False

        finally:
            await browser.close()


def log_tweet(text):
    """Log posted tweet."""
    log = []
    if os.path.exists(TWEET_LOG):
        with open(TWEET_LOG) as f:
            log = json.load(f)
    log.append({
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Keep last 100
    log = log[-100:]
    os.makedirs(os.path.dirname(TWEET_LOG), exist_ok=True)
    with open(TWEET_LOG, "w") as f:
        json.dump(log, f, indent=2)


def get_recent_tweets():
    """Get recent tweet texts for context."""
    if os.path.exists(TWEET_LOG):
        with open(TWEET_LOG) as f:
            log = json.load(f)
        return [t["text"] for t in log[-10:]]
    return []


# ─── Main ─────────────────────────────────────────

async def run_once(dry_run=False, text=None):
    """Generate and post one tweet."""
    if text is None:
        recent = get_recent_tweets()
        text = generate_tweet(recent)
        if not text:
            print("[rin-tweet] Failed to generate tweet")
            return False

    print(f"[rin-tweet] Tweet: {text}")
    return await post_tweet(text, dry_run=dry_run)


async def run_loop():
    """Continuous loop: post every 2-6 hours."""
    print("[rin-tweet] Starting auto-tweet loop...")
    while True:
        success = await run_once()
        interval = random.randint(MIN_INTERVAL, MAX_INTERVAL)
        hours = interval / 3600
        print(f"[rin-tweet] Next tweet in {hours:.1f}h")
        await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="rin auto-tweeter")
    parser.add_argument("--dry-run", action="store_true", help="Generate but don't post")
    parser.add_argument("--loop", action="store_true", help="Auto-post every 2-6 hours")
    parser.add_argument("--text", type=str, help="Post specific text")
    args = parser.parse_args()

    if args.loop:
        asyncio.run(run_loop())
    else:
        asyncio.run(run_once(dry_run=args.dry_run, text=args.text))


if __name__ == "__main__":
    main()
