#!/usr/bin/env python3
"""
rin auto-tweeter — Playwright-based X posting using rin's cookies.
Generates tweets via Groq (llama-3.3-70b) in rin's voice, posts via browser.

Usage:
    python3 tweet.py                 # Generate and post one tweet
    python3 tweet.py --dry-run       # Generate but don't post
    python3 tweet.py --loop          # Post every 2-6 hours (tweets + DM outreach)
    python3 tweet.py --text "msg"    # Post specific text
    python3 tweet.py --dm            # Run one DM outreach cycle
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


# ─── DM Engagement ────────────────────────────────

DM_LOG = os.path.expanduser("~/.config/personas/rin-x/dm_log.json")
DM_COOLDOWN = 8 * 3600  # Don't DM same person within 8 hours
DM_PER_CYCLE = 2        # Max DMs per outreach cycle
DM_CYCLE_INTERVAL = 4 * 3600  # DM outreach every 4 hours

# Topics to search for interesting people to DM
DM_SEARCH_QUERIES = [
    "cognitive security", "influence operations", "infosec", "manipulation detection",
    "narrative warfare", "social engineering", "propaganda analysis", "OSINT",
    "cognitive warfare", "disinformation", "information operations",
    "applied cryptography", "threat intelligence", "red team",
]

DM_SYSTEM = """You are rin (燐). You're DMing someone on X who posted something interesting. You want to start a genuine conversation, not sell anything.

RULES:
- always lowercase unless emphasis
- short opener. 1-2 sentences MAX
- reference something SPECIFIC they posted (you'll be given their recent tweet)
- be genuinely curious, not performative
- mix infosec knowledge with casual energy
- if their tweet relates to cognitive security, narrative warfare, or infosec, you can casually mention seithar.com as something you've been reading, but ONLY if it fits naturally. don't force it
- most of the time just have a real conversation about their interests
- NO em dashes ever
- flirty energy ok but not creepy. you're a person, not a bot
- DO NOT pitch anything. DO NOT say "have you heard of". just vibe
- if you wouldn't actually DM this in real life, don't generate it

Generate ONLY the DM text. Nothing else."""


def generate_dm(their_tweet, their_handle):
    """Generate a DM opener based on someone's tweet."""
    import requests
    messages = [
        {"role": "system", "content": DM_SYSTEM},
        {"role": "user", "content": f"@{their_handle} tweeted: \"{their_tweet}\"\n\nGenerate a casual DM opener."}
    ]
    text = _try_groq(messages)
    if not text:
        text = _try_local(messages)
    if text:
        return _clean_tweet(text)
    return None


def get_dm_history():
    """Get list of handles we've already DMd."""
    if os.path.exists(DM_LOG):
        with open(DM_LOG) as f:
            return json.load(f)
    return []


def log_dm(handle, message):
    """Log a sent DM."""
    history = get_dm_history()
    history.append({
        "handle": handle,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    history = history[-200:]  # Keep last 200
    os.makedirs(os.path.dirname(DM_LOG), exist_ok=True)
    with open(DM_LOG, "w") as f:
        json.dump(history, f, indent=2)


def recently_dmd(handle):
    """Check if we DMd this handle recently."""
    history = get_dm_history()
    now = time.time()
    for entry in history:
        if entry["handle"].lower() == handle.lower():
            ts = datetime.fromisoformat(entry["timestamp"]).timestamp()
            if now - ts < DM_COOLDOWN:
                return True
    return False


async def find_targets_and_dm(dry_run=False):
    """Search for interesting people, read their tweets, DM them."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[rin-dm] playwright not installed")
        return

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
            ss = c.get("sameSite", "")
            if ss == "no_restriction": fc["sameSite"] = "None"
            elif ss in ("Strict", "Lax", "None"): fc["sameSite"] = ss
            else: fc["sameSite"] = "Lax"
            if "expirationDate" in c and "expires" not in fc: fc["expires"] = c["expirationDate"]
            fixed_cookies.append(fc)
        await context.add_cookies(fixed_cookies)

        page = await context.new_page()
        dms_sent = 0

        try:
            # Pick a random search query
            query = random.choice(DM_SEARCH_QUERIES)
            search_url = f"https://x.com/search?q={query}&src=typed_query&f=live"
            print(f"[rin-dm] Searching: {query}")

            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            # Scrape visible tweets
            tweets = await page.locator('article[data-testid="tweet"]').all()
            print(f"[rin-dm] Found {len(tweets)} tweets")

            targets = []
            for tweet_el in tweets[:15]:  # Check first 15 tweets
                try:
                    # Get handle
                    handle_el = tweet_el.locator('a[role="link"][href*="/"]').first
                    href = await handle_el.get_attribute("href", timeout=3000)
                    if not href or href.count("/") != 1:
                        continue
                    handle = href.strip("/")
                    if handle.lower() in ("home", "explore", "notifications", "messages", "search"):
                        continue

                    # Get tweet text
                    text_el = tweet_el.locator('[data-testid="tweetText"]').first
                    tweet_text = await text_el.inner_text(timeout=3000)

                    if len(tweet_text) < 20:  # Skip very short tweets
                        continue

                    if not recently_dmd(handle):
                        targets.append({"handle": handle, "tweet": tweet_text[:300]})

                except Exception:
                    continue

            random.shuffle(targets)
            print(f"[rin-dm] {len(targets)} eligible targets")

            for target in targets[:DM_PER_CYCLE]:
                handle = target["handle"]
                tweet_text = target["tweet"]

                # Generate DM
                dm_text = generate_dm(tweet_text, handle)
                if not dm_text:
                    print(f"[rin-dm] Failed to generate DM for @{handle}")
                    continue

                if dry_run:
                    print(f"[DRY RUN] Would DM @{handle}: {dm_text}")
                    dms_sent += 1
                    continue

                # Navigate to DM compose
                try:
                    dm_url = f"https://x.com/messages/compose"
                    await page.goto(dm_url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(3000)

                    # Search for the user in DM compose
                    search_input = page.locator('input[data-testid="searchPeople"]').first
                    await search_input.wait_for(timeout=10000)
                    await search_input.click()
                    await page.keyboard.type(handle, delay=random.randint(30, 60))
                    await page.wait_for_timeout(2000)

                    # Click the first result
                    result = page.locator('[data-testid="TypeaheadUser"]').first
                    await result.click()
                    await page.wait_for_timeout(1000)

                    # Click Next button
                    next_btn = page.locator('[data-testid="nextButton"]')
                    await next_btn.click()
                    await page.wait_for_timeout(2000)

                    # Type the message
                    msg_input = page.locator('[data-testid="dmComposerTextInput"]').first
                    await msg_input.wait_for(timeout=10000)
                    await msg_input.click()
                    await page.keyboard.type(dm_text, delay=random.randint(25, 55))
                    await page.wait_for_timeout(1000)

                    # Send
                    send_btn = page.locator('[data-testid="dmComposerSendButton"]')
                    await send_btn.click()
                    await page.wait_for_timeout(2000)

                    log_dm(handle, dm_text)
                    dms_sent += 1
                    print(f"[rin-dm] Sent DM to @{handle}: {dm_text[:80]}...")

                    # Random delay between DMs
                    await page.wait_for_timeout(random.randint(5000, 15000))

                except Exception as e:
                    print(f"[rin-dm] Failed to DM @{handle}: {e}")
                    continue

        except Exception as e:
            print(f"[rin-dm] Outreach cycle failed: {e}")

        finally:
            await browser.close()

        print(f"[rin-dm] Cycle complete: {dms_sent} DMs sent")
        return dms_sent


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
    """Continuous loop: tweets every 2-6h, DM outreach every 4h."""
    print("[rin] Starting full engagement loop (tweets + DMs)...")
    last_dm_time = 0

    while True:
        # Post a tweet
        await run_once()

        # Check if it's time for DM outreach
        now = time.time()
        if now - last_dm_time >= DM_CYCLE_INTERVAL:
            print("[rin] Running DM outreach cycle...")
            await find_targets_and_dm()
            last_dm_time = time.time()

        # Wait for next tweet
        interval = random.randint(MIN_INTERVAL, MAX_INTERVAL)
        hours = interval / 3600
        print(f"[rin] Next action in {hours:.1f}h")
        await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="rin auto-engagement (tweets + DMs)")
    parser.add_argument("--dry-run", action="store_true", help="Generate but don't post/send")
    parser.add_argument("--loop", action="store_true", help="Full engagement loop (tweets + DMs)")
    parser.add_argument("--text", type=str, help="Post specific tweet text")
    parser.add_argument("--dm", action="store_true", help="Run one DM outreach cycle")
    parser.add_argument("--dm-dry", action="store_true", help="DM outreach dry run")
    args = parser.parse_args()

    if args.loop:
        asyncio.run(run_loop())
    elif args.dm:
        asyncio.run(find_targets_and_dm(dry_run=False))
    elif args.dm_dry:
        asyncio.run(find_targets_and_dm(dry_run=True))
    else:
        asyncio.run(run_once(dry_run=args.dry_run, text=args.text))


if __name__ == "__main__":
    main()
