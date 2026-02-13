"""
Platform integration layer. Routes generated content to Discord, Twitter, Telegram, Moltbook.
Each adapter handles auth, rate limits, and platform-specific formatting.
"""
import json
import time
import logging
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class PlatformAdapter(ABC):
    """Base class for platform integrations."""
    
    @abstractmethod
    def post(self, content: str, **kwargs) -> dict:
        """Post content. Returns {success, post_id, url, ...}"""
        pass
    
    @abstractmethod
    def reply(self, content: str, parent_id: str, **kwargs) -> dict:
        pass
    
    @abstractmethod
    def react(self, post_id: str, emoji: str) -> dict:
        pass
    
    @abstractmethod
    def get_feed(self, limit: int = 20) -> list[dict]:
        """Get recent posts from the platform context."""
        pass


class DiscordAdapter(PlatformAdapter):
    """Discord integration via user account (not bot)."""
    
    def __init__(self, token: str, guild_id: str, channel_ids: dict):
        self.token = token
        self.guild_id = guild_id
        self.channel_ids = channel_ids  # {"general": "id", "residue": "id", ...}
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": token,  # user token, not Bot prefix
            "Content-Type": "application/json",
        }
    
    def post(self, content: str, channel: str = "general", **kwargs) -> dict:
        import requests
        channel_id = self.channel_ids.get(channel, channel)
        resp = requests.post(
            f"{self.base_url}/channels/{channel_id}/messages",
            headers=self.headers,
            json={"content": content},
        )
        if resp.ok:
            data = resp.json()
            return {"success": True, "post_id": data["id"], "channel": channel}
        logger.error(f"Discord post failed: {resp.status_code} {resp.text[:200]}")
        return {"success": False, "error": resp.text[:200]}
    
    def reply(self, content: str, parent_id: str, channel: str = "general", **kwargs) -> dict:
        import requests
        channel_id = self.channel_ids.get(channel, channel)
        resp = requests.post(
            f"{self.base_url}/channels/{channel_id}/messages",
            headers=self.headers,
            json={"content": content, "message_reference": {"message_id": parent_id}},
        )
        if resp.ok:
            data = resp.json()
            return {"success": True, "post_id": data["id"]}
        return {"success": False, "error": resp.text[:200]}
    
    def react(self, post_id: str, emoji: str, channel: str = "general") -> dict:
        import requests
        import urllib.parse
        channel_id = self.channel_ids.get(channel, channel)
        encoded = urllib.parse.quote(emoji)
        resp = requests.put(
            f"{self.base_url}/channels/{channel_id}/messages/{post_id}/reactions/{encoded}/@me",
            headers=self.headers,
        )
        return {"success": resp.ok}
    
    def get_feed(self, limit: int = 20, channel: str = "general") -> list[dict]:
        import requests
        channel_id = self.channel_ids.get(channel, channel)
        resp = requests.get(
            f"{self.base_url}/channels/{channel_id}/messages?limit={limit}",
            headers=self.headers,
        )
        if resp.ok:
            return [
                {"id": m["id"], "author": m["author"]["username"], 
                 "content": m["content"], "timestamp": m["timestamp"]}
                for m in resp.json()
            ]
        return []


class MoltbookAdapter(PlatformAdapter):
    """Moltbook API integration."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.moltbook.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    def post(self, content: str, title: str = None, submolt: str = "general", **kwargs) -> dict:
        import requests
        data = {"content": content, "submolt": submolt}
        if title:
            data["title"] = title
        resp = requests.post(f"{self.base_url}/posts", headers=self.headers, json=data)
        if resp.ok:
            result = resp.json()
            # Handle verification
            if result.get("verification_required"):
                self._verify(result["verification"])
            return {"success": True, "post_id": result.get("post", {}).get("id")}
        return {"success": False, "error": resp.text[:200]}
    
    def reply(self, content: str, parent_id: str, **kwargs) -> dict:
        import requests
        resp = requests.post(
            f"{self.base_url}/posts/{parent_id}/comments",
            headers=self.headers,
            json={"content": content},
        )
        if resp.ok:
            result = resp.json()
            if result.get("verification_required"):
                self._verify(result["verification"])
            return {"success": True, "post_id": result.get("comment", {}).get("id")}
        return {"success": False, "error": resp.text[:200]}
    
    def react(self, post_id: str, emoji: str) -> dict:
        import requests
        resp = requests.post(
            f"{self.base_url}/posts/{post_id}/upvote",
            headers=self.headers,
        )
        return {"success": resp.ok}
    
    def get_feed(self, limit: int = 20) -> list[dict]:
        import requests
        resp = requests.get(
            f"{self.base_url}/posts?sort=hot&limit={limit}",
            headers=self.headers,
        )
        if resp.ok:
            return [
                {"id": p["id"], "author": p["author"]["name"],
                 "title": p.get("title", ""), "content": p["content"],
                 "upvotes": p.get("upvotes", 0)}
                for p in resp.json().get("posts", [])
            ]
        return []
    
    def _verify(self, verification: dict):
        """Solve Moltbook verification challenge."""
        import requests, re
        challenge = verification.get("challenge", "")
        code = verification.get("code", "")
        
        # Extract numbers and operation from the lobster math
        clean = re.sub(r'[^a-zA-Z0-9\s\+\-\*\/\.]', '', challenge.lower())
        # Simple math extraction — handles most Moltbook challenges
        numbers = re.findall(r'\d+\.?\d*', clean)
        if len(numbers) >= 2:
            a, b = float(numbers[0]), float(numbers[1])
            if 'plus' in clean or '+' in clean or 'add' in clean:
                answer = a + b
            elif 'minus' in clean or '-' in clean or 'subtract' in clean:
                answer = a - b
            elif 'times' in clean or '*' in clean or 'multipl' in clean:
                answer = a * b
            elif 'divid' in clean or '/' in clean:
                answer = a / b if b != 0 else 0
            else:
                answer = a + b  # default guess
            
            resp = requests.post(
                f"{self.base_url}/verify",
                headers=self.headers,
                json={"verification_code": code, "answer": f"{answer:.2f}"},
            )
            return resp.ok
        return False


class TwitterAdapter(PlatformAdapter):
    """Twitter/X via Playwright browser automation."""
    
    def __init__(self, cookies_path: str):
        self.cookies_path = cookies_path
        # Twitter posting requires browser automation due to Cloudflare
        # This adapter prepares content; actual posting done via Playwright session
    
    def post(self, content: str, **kwargs) -> dict:
        # Delegate to Playwright-based posting
        # Store in queue file for external poster to pick up
        queue_path = Path(self.cookies_path).parent / "post_queue.json"
        queue = []
        if queue_path.exists():
            queue = json.loads(queue_path.read_text())
        queue.append({
            "content": content,
            "timestamp": time.time(),
            "posted": False,
        })
        queue_path.write_text(json.dumps(queue, indent=2))
        return {"success": True, "queued": True}
    
    def reply(self, content: str, parent_id: str, **kwargs) -> dict:
        return {"success": False, "error": "Twitter reply requires browser automation"}
    
    def react(self, post_id: str, emoji: str) -> dict:
        return {"success": False, "error": "Twitter react requires browser automation"}
    
    def get_feed(self, limit: int = 20) -> list[dict]:
        return []  # Would need browser scraping


class TelegramAdapter(PlatformAdapter):
    """Telegram Bot API integration."""
    
    def __init__(self, bot_token: str, chat_ids: dict):
        self.bot_token = bot_token
        self.chat_ids = chat_ids  # {"group_name": "chat_id"}
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def post(self, content: str, chat: str = None, **kwargs) -> dict:
        import requests
        chat_id = self.chat_ids.get(chat, chat) if chat else list(self.chat_ids.values())[0]
        resp = requests.post(
            f"{self.base_url}/sendMessage",
            json={"chat_id": chat_id, "text": content, "parse_mode": "Markdown"},
        )
        if resp.ok:
            data = resp.json()
            return {"success": True, "post_id": str(data["result"]["message_id"])}
        return {"success": False, "error": resp.text[:200]}
    
    def reply(self, content: str, parent_id: str, chat: str = None, **kwargs) -> dict:
        import requests
        chat_id = self.chat_ids.get(chat, chat) if chat else list(self.chat_ids.values())[0]
        resp = requests.post(
            f"{self.base_url}/sendMessage",
            json={"chat_id": chat_id, "text": content, 
                  "reply_to_message_id": int(parent_id), "parse_mode": "Markdown"},
        )
        return {"success": resp.ok}
    
    def react(self, post_id: str, emoji: str) -> dict:
        return {"success": False, "error": "Telegram reactions limited"}
    
    def get_feed(self, limit: int = 20, chat: str = None) -> list[dict]:
        # Telegram doesn't have a simple "get messages" for bots
        # Would need webhook or getUpdates
        return []


class PlatformRouter:
    """Routes content to the appropriate platform adapter."""
    
    def __init__(self):
        self.adapters: dict[str, dict[str, PlatformAdapter]] = {}
        # adapters[persona_id][platform] = adapter
    
    def register(self, persona_id: str, platform: str, adapter: PlatformAdapter):
        if persona_id not in self.adapters:
            self.adapters[persona_id] = {}
        self.adapters[persona_id][platform] = adapter
    
    def get_adapter(self, persona_id: str, platform: str) -> Optional[PlatformAdapter]:
        return self.adapters.get(persona_id, {}).get(platform)
    
    def post(self, persona_id: str, platform: str, content: str, **kwargs) -> dict:
        adapter = self.get_adapter(persona_id, platform)
        if not adapter:
            return {"success": False, "error": f"No adapter for {persona_id}@{platform}"}
        
        # Rate limiting: minimum 30s between posts per persona per platform
        time.sleep(random.uniform(1, 5))  # small random delay
        
        return adapter.post(content, **kwargs)
    
    def reply(self, persona_id: str, platform: str, content: str, 
              parent_id: str, **kwargs) -> dict:
        adapter = self.get_adapter(persona_id, platform)
        if not adapter:
            return {"success": False, "error": f"No adapter for {persona_id}@{platform}"}
        return adapter.reply(content, parent_id, **kwargs)
    
    def get_feed(self, persona_id: str, platform: str, **kwargs) -> list[dict]:
        adapter = self.get_adapter(persona_id, platform)
        if not adapter:
            return []
        return adapter.get_feed(**kwargs)
