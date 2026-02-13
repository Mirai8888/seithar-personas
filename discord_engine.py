"""
Seithar Persona Engine — Generic Discord selfbot orchestrator
Drop a persona config JSON + run. That's it.

Usage:
    python3 engine.py --persona rin
    python3 engine.py --persona voidfront
    python3 engine.py --config /path/to/persona.json

Each persona needs:
    ~/.openclaw/workspace/personas/<name>/persona.json
"""

import discord
import json
import random
import asyncio
import argparse
import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime

# ─── Globals ──────────────────────────────────────

GROQ_CREDS = os.path.expanduser("~/.config/fleshengine/credentials.json")
PERSONAS_DIR = os.path.expanduser("~/.openclaw/workspace/personas")
GUILD_ID = 1444739404576067647

with open(GROQ_CREDS) as f:
    GROQ_KEY = json.load(f)["groq_api_key"]


# ─── Persona Config Schema ───────────────────────
#
# persona.json:
# {
#   "name": "rin",
#   "token_file": "~/.config/personas/egirl-01.json",
#   "token_key": "token",
#
#   "channels": {
#     "active": ["residue"],          # respond here
#     "lurk": ["directives"],         # react only
#     "ignore": []                    # skip entirely
#   },
#
#   "behavior": {
#     "react_probability": 0.12,
#     "unprompted_probability": 0.03,
#     "cooldown_seconds": 120,
#     "min_delay": 2.0,
#     "max_delay": 6.0,
#     "min_typing": 1.5,
#     "max_typing": 5.0,
#     "max_response_length": 150,
#     "reply_probability": 0.6,
#     "reactions": ["🫧", "✨", "🖤", "💿"],
#     "interest_keywords": ["seithar", "crypto", "infosec"]
#   },
#
#   "voice": {
#     "system_prompt": "You are rin...",
#     "model": "llama-3.3-70b-versatile",
#     "temperature": 0.9
#   }
# }


def load_persona(name=None, config_path=None):
    """Load persona config from name or path."""
    if config_path:
        path = Path(config_path)
    elif name:
        path = Path(PERSONAS_DIR) / name / "persona.json"
    else:
        raise ValueError("need --persona or --config")

    if not path.exists():
        print(f"[engine] persona config not found: {path}")
        sys.exit(1)

    with open(path) as f:
        config = json.load(f)

    # Load token
    token_file = os.path.expanduser(config["token_file"])
    with open(token_file) as f:
        token_data = json.load(f)
    config["_token"] = token_data[config.get("token_key", "token")]

    print(f"[engine] loaded persona: {config['name']}")
    return config


def generate_response(config, context_messages, user_message, user_name):
    """Generate persona response via Groq."""
    voice = config["voice"]
    messages = [{"role": "system", "content": voice["system_prompt"]}]

    for msg in context_messages[-10:]:
        role = "assistant" if msg["is_self"] else "user"
        content = msg["content"]
        if not msg["is_self"]:
            content = f"[{msg['author']}]: {content}"
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": f"[{user_name}]: {user_message}"})

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": voice.get("model", "llama-3.3-70b-versatile"),
                "messages": messages,
                "max_tokens": config["behavior"].get("max_response_length", 150),
                "temperature": voice.get("temperature", 0.9),
                "top_p": 0.95
            },
            timeout=15
        )
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"].strip()
            # Strip roleplay markers
            name = config["name"]
            for prefix in [f"{name}:", f"{name} :", f"**{name}**:", f"[{name}]:"]:
                if text.lower().startswith(prefix.lower()):
                    text = text[len(prefix):].strip()
            text = text.strip('"').strip("'")
            return text
        else:
            print(f"[{config['name']}] groq error: {r.status_code} {r.text[:200]}")
            return None
    except Exception as e:
        print(f"[{config['name']}] groq failed: {e}")
        return None


class PersonaBot(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.name = config["name"]
        self.behavior = config["behavior"]
        self.channels = config["channels"]
        self.last_response_time = 0
        self.channel_history = {}

    async def on_ready(self):
        print(f"[{self.name}] online as {self.user} ({self.user.id})")

    async def on_message(self, message):
        # Track own messages
        if message.author == self.user:
            self._track(message, is_self=True)
            return

        # Only our guild
        if not message.guild or message.guild.id != GUILD_ID:
            return

        ch = message.channel.name
        self._track(message, is_self=False)

        # Ignore channels
        if ch in self.channels.get("ignore", []):
            return

        # Lurk channels: react only
        if ch in self.channels.get("lurk", []):
            if random.random() < self.behavior.get("react_probability", 0.1):
                await self._react(message)
            return

        # Active channels
        if ch not in self.channels.get("active", []):
            return

        # Maybe react (independent of responding)
        if random.random() < self.behavior.get("react_probability", 0.1):
            await self._react(message)

        # Should we respond?
        if not self._should_respond(message):
            return

        # Cooldown (skip if directly mentioned)
        now = time.time()
        directly_addressed = (
            self.user.mentioned_in(message) or
            self.name.lower() in message.content.lower().split()
        )
        if not directly_addressed:
            cd = self.behavior.get("cooldown_seconds", 120)
            if now - self.last_response_time < cd:
                return

        # Generate
        ctx = self.channel_history.get(message.channel.id, [])
        response = generate_response(
            self.config, ctx,
            message.content, message.author.display_name
        )
        if not response:
            return

        # Human delays
        delay = random.uniform(
            self.behavior.get("min_delay", 2.0),
            self.behavior.get("max_delay", 6.0)
        )
        await asyncio.sleep(delay)

        typing_time = random.uniform(
            self.behavior.get("min_typing", 1.5),
            self.behavior.get("max_typing", 5.0)
        )
        typing_time += len(response) * 0.02
        typing_time = min(typing_time, 10.0)

        async with message.channel.typing():
            await asyncio.sleep(typing_time)

        try:
            reply_prob = self.behavior.get("reply_probability", 0.6)
            if directly_addressed or random.random() < reply_prob:
                await message.reply(response, mention_author=False)
            else:
                await message.channel.send(response)

            self.last_response_time = time.time()
            self._track_raw(message.channel.id, response)
            print(f"[{self.name}] #{ch}: {response[:80]}")
        except Exception as e:
            print(f"[{self.name}] send error: {e}")

    def _should_respond(self, message):
        content = message.content.lower()

        # Direct mention
        if self.user.mentioned_in(message):
            return True

        # Name mentioned
        if self.name.lower() in content.split():
            return True

        # Interest keywords
        keywords = self.behavior.get("interest_keywords", [])
        if any(kw in content for kw in keywords):
            prob = self.behavior.get("unprompted_probability", 0.03) * 3
            if random.random() < prob:
                return True

        # Random
        if random.random() < self.behavior.get("unprompted_probability", 0.03):
            return True

        return False

    async def _react(self, message):
        reactions = self.behavior.get("reactions", ["👍"])
        try:
            await message.add_reaction(random.choice(reactions))
        except:
            pass

    def _track(self, message, is_self=False):
        cid = message.channel.id
        if cid not in self.channel_history:
            self.channel_history[cid] = []
        self.channel_history[cid].append({
            "author": message.author.display_name,
            "content": message.content[:500],
            "is_self": is_self,
            "timestamp": time.time()
        })
        self.channel_history[cid] = self.channel_history[cid][-20:]

    def _track_raw(self, channel_id, content):
        if channel_id not in self.channel_history:
            self.channel_history[channel_id] = []
        self.channel_history[channel_id].append({
            "author": self.name,
            "content": content[:500],
            "is_self": True,
            "timestamp": time.time()
        })
        self.channel_history[channel_id] = self.channel_history[channel_id][-20:]


def main():
    parser = argparse.ArgumentParser(description="Seithar Persona Engine")
    parser.add_argument("--persona", help="Persona name (loads from personas/<name>/persona.json)")
    parser.add_argument("--config", help="Direct path to persona config JSON")
    args = parser.parse_args()

    config = load_persona(name=args.persona, config_path=args.config)
    bot = PersonaBot(config)
    bot.run(config["_token"])


if __name__ == "__main__":
    main()
