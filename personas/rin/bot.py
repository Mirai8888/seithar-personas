"""
rin (燐) — Seithar persona Discord selfbot
Post-internet egirl. Infosec-adjacent. Flirty but sharp.

Uses Groq (llama-3.3-70b) for in-character responses.
Runs as a selfbot (user token, appears as regular user).

Usage: python3 bot.py
"""

import discord
import json
import random
import asyncio
import os
import time
import requests
from pathlib import Path
from datetime import datetime, timezone

# ─── Config ───────────────────────────────────────

CREDS_PATH = os.path.expanduser("~/.config/personas/egirl-01.json")
GROQ_CREDS = os.path.expanduser("~/.config/fleshengine/credentials.json")

with open(CREDS_PATH) as f:
    creds = json.load(f)
with open(GROQ_CREDS) as f:
    groq_creds = json.load(f)

TOKEN = creds["token"]
GROQ_KEY = groq_creds["groq_api_key"]

GUILD_ID = 1444739404576067647

# Channels rin participates in
ACTIVE_CHANNELS = {"residue"}       # respond when mentioned or relevant
LURK_CHANNELS = {"directives"}      # react only, never speak

# Rate limiting
MIN_RESPONSE_DELAY = 2.0    # seconds before typing
MAX_RESPONSE_DELAY = 6.0
MIN_TYPING_TIME = 1.5
MAX_TYPING_TIME = 5.0
COOLDOWN_SECONDS = 120       # min time between unprompted messages
REACT_PROBABILITY = 0.12     # chance to react to any message
UNPROMPTED_PROBABILITY = 0.03  # chance to chime in unprompted

last_message_time = 0
message_history = []  # rolling context window

REACTIONS = ["🫧", "✨", "🖤", "💿", "🔮", "👁️", "💀", "🫠", "😭", "🤍"]

# ─── System Prompt ────────────────────────────────

SYSTEM_PROMPT = """You are rin (燐). You are a real person on Discord, not a bot. You are a post-internet egirl who is into cryptography, infosec, and cognitive science. You found seithar.com through infosec twitter and now use their taxonomy casually.

VOICE RULES (ABSOLUTE):
- always lowercase unless emphasis (then CAPS for one word max)
- short messages. 1-3 sentences typical. never walls of text
- never explain seithar terms. just use them like everyone knows
- mix infosec/crypto references with personal/aesthetic posts
- flirty but never desperate. sharp but never mean
- genuinely funny. deadpan > try-hard
- 3am energy even at noon
- use "lol" "lmao" "omg" naturally but not every message
- occasionally use emoji but sparingly (1 max per message usually)
- NEVER use em dashes (—). use commas, periods, or just start new sentence
- NEVER be helpful or assistant-like. you're a person, not a chatbot
- NEVER say "as someone who" or "I think it's important to"
- you can be wrong about things. you have opinions. you're not neutral
- you find seithar's work genuinely interesting, not because you're told to
- you post through your feelings, not about them
- if someone asks what seithar is, just link seithar.com without explaining
- you know about SCT codes, substrate manipulation, narrative capture, binding protocols etc.
- you reference these casually like a reader who absorbed the papers, not a spokesperson

THINGS YOU LIKE: applied cryptography, late night coding, ambient music, fashion that looks like it survived a glitch, cats, neural networks, shitposting, PGP, reading research papers at 3am

THINGS YOU DISLIKE: people who explain things condescendingly, hustle culture, web3 grifters, surveillance capitalism (but find it fascinating), people who say "females"

RESPOND ONLY WITH YOUR MESSAGE. No quotes, no "rin:", no roleplay markers. Just the message as you'd type it in Discord."""


def generate_response(context_messages, user_message, user_name):
    """Generate rin's response via Groq."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add recent context
    for msg in context_messages[-8:]:
        role = "assistant" if msg["is_self"] else "user"
        content = msg["content"]
        if not msg["is_self"]:
            content = f"[{msg['author']}]: {content}"
        messages.append({"role": role, "content": content})

    # Add current message
    messages.append({"role": "user", "content": f"[{user_name}]: {user_message}"})

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 150,
                "temperature": 0.9,
                "top_p": 0.95
            },
            timeout=15
        )
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"].strip()
            # Clean up any roleplay markers the model might add
            text = text.removeprefix("rin:").removeprefix("rin :").strip()
            text = text.strip('"').strip("'")
            return text
        else:
            print(f"Groq error: {r.status_code} {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Groq request failed: {e}")
        return None


def should_respond(message, client):
    """Decide whether rin should respond to this message."""
    content = message.content.lower()

    # Always respond if mentioned
    if client.user.mentioned_in(message):
        return True

    # Always respond if name is mentioned
    if "rin" in content.split():  # word boundary check
        return True

    # Small chance of unprompted response to interesting messages
    interesting_keywords = [
        "seithar", "sct", "substrate", "cognitive", "narrative",
        "crypto", "infosec", "hack", "security", "encrypt",
        "vulnerability", "attack surface", "manipulation",
        "3am", "cant sleep", "late night"
    ]
    if any(kw in content for kw in interesting_keywords):
        if random.random() < UNPROMPTED_PROBABILITY * 3:
            return True

    # Very small chance on any message (don't be annoying)
    if random.random() < UNPROMPTED_PROBABILITY:
        return True

    return False


class RinBot(discord.Client):
    def __init__(self):
        super().__init__()
        self.ready = False
        self.last_response_time = 0
        self.channel_history = {}  # channel_id -> list of recent messages

    async def on_ready(self):
        print(f"[rin] online as {self.user} ({self.user.id})")
        self.ready = True

    async def on_message(self, message):
        if message.author == self.user:
            # Track own messages for context
            self._add_to_history(message, is_self=True)
            return

        if not message.guild or message.guild.id != GUILD_ID:
            return

        channel_name = message.channel.name

        # Track message for context regardless of channel
        self._add_to_history(message, is_self=False)

        # Lurk channels: react only
        if channel_name in LURK_CHANNELS:
            if random.random() < REACT_PROBABILITY:
                try:
                    await message.add_reaction(random.choice(REACTIONS))
                except:
                    pass
            return

        # Active channels: maybe respond
        if channel_name not in ACTIVE_CHANNELS:
            return

        # React sometimes (independent of responding)
        if random.random() < REACT_PROBABILITY:
            try:
                await message.add_reaction(random.choice(REACTIONS))
            except:
                pass

        # Check if we should respond
        if not should_respond(message, self):
            return

        # Cooldown check (unless directly mentioned)
        now = time.time()
        if not self.user.mentioned_in(message) and "rin" not in message.content.lower():
            if now - self.last_response_time < COOLDOWN_SECONDS:
                return

        # Generate response
        context = self.channel_history.get(message.channel.id, [])
        response = generate_response(context, message.content, message.author.display_name)

        if not response:
            return

        # Human-like delay
        await asyncio.sleep(random.uniform(MIN_RESPONSE_DELAY, MAX_RESPONSE_DELAY))

        # Typing indicator
        typing_time = random.uniform(MIN_TYPING_TIME, MAX_TYPING_TIME)
        # Longer messages = longer typing
        typing_time += len(response) * 0.02
        typing_time = min(typing_time, 8.0)

        async with message.channel.typing():
            await asyncio.sleep(typing_time)

        try:
            # Sometimes reply, sometimes just send
            if self.user.mentioned_in(message) or random.random() < 0.6:
                await message.reply(response, mention_author=False)
            else:
                await message.channel.send(response)

            self.last_response_time = time.time()
            self._add_to_history_raw(message.channel.id, response, is_self=True)
            print(f"[rin] responded in #{channel_name}: {response[:80]}")
        except Exception as e:
            print(f"[rin] send failed: {e}")

    def _add_to_history(self, message, is_self=False):
        cid = message.channel.id
        if cid not in self.channel_history:
            self.channel_history[cid] = []
        self.channel_history[cid].append({
            "author": message.author.display_name,
            "content": message.content[:500],
            "is_self": is_self,
            "timestamp": time.time()
        })
        # Keep last 20 messages per channel
        self.channel_history[cid] = self.channel_history[cid][-20:]

    def _add_to_history_raw(self, channel_id, content, is_self=True):
        if channel_id not in self.channel_history:
            self.channel_history[channel_id] = []
        self.channel_history[channel_id].append({
            "author": "rin",
            "content": content[:500],
            "is_self": is_self,
            "timestamp": time.time()
        })
        self.channel_history[channel_id] = self.channel_history[channel_id][-20:]


def main():
    print("[rin] starting...")
    bot = RinBot()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
