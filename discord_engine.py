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
        # Support both old "channels" format and new "guilds" format
        if "guilds" in config:
            self.guilds_config = config["guilds"]
            self.channels = None
        else:
            self.guilds_config = None
            self.channels = config.get("channels", {"active": [], "lurk": [], "ignore": []})
        self.last_response_time = 0
        self.channel_history = {}

    def _get_channel_config(self, guild_id, channel_name):
        """Get channel role (active/lurk/ignore/unknown) for a given guild+channel."""
        if self.guilds_config:
            gid = str(guild_id)
            # Check specific guild first, then wildcard
            guild_cfg = self.guilds_config.get(gid, self.guilds_config.get("*", None))
            if guild_cfg is None:
                return "unknown"
            if channel_name in guild_cfg.get("ignore", []):
                return "ignore"
            if channel_name in guild_cfg.get("lurk", []):
                return "lurk"
            if channel_name in guild_cfg.get("active", []):
                return "active"
            # Wildcard guild: unlisted channels default to active
            # (she should participate in any server she's added to)
            # Specific guild: unlisted channels default to lurk
            if gid not in self.guilds_config:
                # Using wildcard config, unlisted channel = active
                return "active"
            return "lurk"
        else:
            # Legacy single-guild format
            if channel_name in self.channels.get("ignore", []):
                return "ignore"
            if channel_name in self.channels.get("lurk", []):
                return "lurk"
            if channel_name in self.channels.get("active", []):
                return "active"
            return "unknown"

    async def on_ready(self):
        guilds = [g.name for g in self.guilds]
        print(f"[{self.name}] online as {self.user} ({self.user.id})", flush=True)
        print(f"[{self.name}] in {len(guilds)} servers: {', '.join(guilds)}", flush=True)

        # Auto-join servers from invite list
        invites = self.config.get("invites", [])
        for invite_url in invites:
            code = invite_url.split("/")[-1]
            guild_ids = [str(g.id) for g in self.guilds]
            try:
                import requests as req
                headers = {"Authorization": self.config["_token"], "User-Agent": "Mozilla/5.0"}
                # Check invite info first
                info = req.get(f"https://discord.com/api/v10/invites/{code}", headers=headers).json()
                guild_id = info.get("guild", {}).get("id", "")
                if guild_id in guild_ids:
                    continue  # already in this server
                # Try to join
                r = req.post(f"https://discord.com/api/v10/invites/{code}", headers=headers, json={})
                if r.status_code == 200:
                    print(f"[{self.name}] joined {info.get('guild',{}).get('name','unknown')} via invite", flush=True)
                else:
                    print(f"[{self.name}] failed to join {code}: {r.status_code}", flush=True)
            except Exception as e:
                print(f"[{self.name}] invite join error: {e}", flush=True)

    async def on_message(self, message):
        # Track own messages
        if message.author == self.user:
            self._track(message, is_self=True)
            return

        # Only guild messages
        if not message.guild:
            return

        # Legacy: skip non-target guild if using old format
        if self.channels and message.guild.id != GUILD_ID:
            return

        ch = message.channel.name
        self._track(message, is_self=False)

        role = self._get_channel_config(message.guild.id, ch)

        # Ignore
        if role == "ignore" or role == "unknown":
            return

        # Lurk: react only
        if role == "lurk":
            if random.random() < self.behavior.get("react_probability", 0.1):
                await self._react(message)
            return

        # Active channel

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

        # Direct mention - always respond
        if self.user.mentioned_in(message):
            return True

        # Name mentioned
        if self.name.lower() in content.split():
            return True

        # Reply to rin's message - always respond
        if message.reference and message.reference.resolved:
            if hasattr(message.reference.resolved, 'author'):
                if message.reference.resolved.author == self.user:
                    return True

        # Interest keywords
        keywords = self.behavior.get("interest_keywords", [])
        if any(kw in content for kw in keywords):
            prob = self.behavior.get("unprompted_probability", 0.03) * 3
            if random.random() < prob:
                return True

        # Higher engagement in external servers (not home guild)
        is_home = message.guild and message.guild.id == GUILD_ID
        base_prob = self.behavior.get("unprompted_probability", 0.03)
        if not is_home:
            base_prob *= 2.5  # more active in external servers to build presence

        # Respond to questions more often
        if "?" in content:
            base_prob *= 2

        # Respond in active conversations (multiple recent messages)
        ctx = self.channel_history.get(message.channel.id, [])
        if len(ctx) >= 5:
            recent = [m for m in ctx[-5:] if time.time() - m["timestamp"] < 120]
            if len(recent) >= 3:
                base_prob *= 1.5  # active conversation boost

        if random.random() < base_prob:
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
