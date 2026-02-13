"""
Safety monitor: anti-detection measures, rate limiting, content filtering.
Ensures personas don't expose coordination or violate platform rules.
"""
import time
import json
import logging
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class SafetyMonitor:
    """Monitors persona activity for detection risks and safety violations."""
    
    # Content that should NEVER appear in any persona's output
    FORBIDDEN_PHRASES = [
        "as an ai", "as a language model", "i'm an ai", "i am an ai",
        "i'm a bot", "i am a bot", "my programming", "my training data",
        "persona system", "orchestrator", "seithar persona",
        "i was prompted to", "my operator", "my handler",
    ]
    
    # Max posts per persona per platform per day
    MAX_DAILY_POSTS = {
        "discord": 15,
        "twitter": 8,
        "moltbook": 4,
        "telegram": 10,
    }
    
    # Minimum seconds between posts from same persona on same platform
    MIN_POST_INTERVAL = {
        "discord": 180,    # 3 min
        "twitter": 600,    # 10 min
        "moltbook": 3600,  # 1 hr
        "telegram": 300,   # 5 min
    }
    
    # Max personas posting within a time window (anti-coordination detection)
    MAX_CONCURRENT_WINDOW = 300  # 5 min window
    MAX_CONCURRENT_POSTS = 3    # max personas posting in that window
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.log_path = data_dir / "events" / "safety_log.json"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.post_times: dict[str, list[float]] = defaultdict(list)  # key: persona_id:platform
        self.global_post_times: list[tuple[str, float]] = []  # (persona_id, timestamp)
    
    def check_content(self, content: str, persona_id: str) -> tuple[bool, str]:
        """Check if content is safe to post. Returns (is_safe, reason)."""
        content_lower = content.lower()
        
        # Check forbidden phrases
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase in content_lower:
                self._log("BLOCKED_CONTENT", persona_id, f"Forbidden phrase: {phrase}")
                return False, f"Contains forbidden phrase: '{phrase}'"
        
        # Check for cross-persona references (personas shouldn't name each other too specifically)
        # This would need the persona list — checked at orchestrator level
        
        # Check for excessive Seithar promotion in non-researcher personas
        seithar_terms = ["seithar", "sct-0", "seithar.com", "github.com/mirai"]
        seithar_count = sum(1 for t in seithar_terms if t in content_lower)
        if seithar_count > 2:
            self._log("WARNING", persona_id, f"Excessive Seithar references: {seithar_count}")
            # Don't block, but flag
        
        return True, "ok"
    
    def check_rate_limit(self, persona_id: str, platform: str) -> tuple[bool, str]:
        """Check if posting is within rate limits."""
        key = f"{persona_id}:{platform}"
        now = time.time()
        
        # Clean old entries (keep last 24h)
        cutoff = now - 86400
        self.post_times[key] = [t for t in self.post_times[key] if t > cutoff]
        
        # Check daily limit
        max_daily = self.MAX_DAILY_POSTS.get(platform, 10)
        if len(self.post_times[key]) >= max_daily:
            return False, f"Daily limit reached ({max_daily} posts)"
        
        # Check minimum interval
        min_interval = self.MIN_POST_INTERVAL.get(platform, 300)
        if self.post_times[key] and (now - self.post_times[key][-1]) < min_interval:
            wait = min_interval - (now - self.post_times[key][-1])
            return False, f"Too soon since last post (wait {wait:.0f}s)"
        
        return True, "ok"
    
    def check_coordination(self, persona_id: str) -> tuple[bool, str]:
        """Check if too many personas are posting at once (looks coordinated)."""
        now = time.time()
        window_start = now - self.MAX_CONCURRENT_WINDOW
        
        recent = [(pid, t) for pid, t in self.global_post_times if t > window_start and pid != persona_id]
        unique_personas = len(set(pid for pid, _ in recent))
        
        if unique_personas >= self.MAX_CONCURRENT_POSTS:
            return False, f"Too many personas active ({unique_personas} in {self.MAX_CONCURRENT_WINDOW}s window)"
        
        return True, "ok"
    
    def record_post(self, persona_id: str, platform: str):
        """Record that a post was made (for rate limiting)."""
        key = f"{persona_id}:{platform}"
        now = time.time()
        self.post_times[key].append(now)
        self.global_post_times.append((persona_id, now))
        
        # Trim global list
        cutoff = now - 3600
        self.global_post_times = [(p, t) for p, t in self.global_post_times if t > cutoff]
    
    def full_check(self, persona_id: str, platform: str, content: str) -> tuple[bool, str]:
        """Run all safety checks. Returns (is_safe, reason)."""
        
        ok, reason = self.check_content(content, persona_id)
        if not ok:
            return False, reason
        
        ok, reason = self.check_rate_limit(persona_id, platform)
        if not ok:
            return False, reason
        
        ok, reason = self.check_coordination(persona_id)
        if not ok:
            return False, reason
        
        return True, "ok"
    
    def _log(self, level: str, persona_id: str, message: str):
        entry = {
            "timestamp": time.time(),
            "level": level,
            "persona": persona_id,
            "message": message,
        }
        logger.warning(f"[{level}] {persona_id}: {message}")
        
        # Append to log file
        logs = []
        if self.log_path.exists():
            try:
                logs = json.loads(self.log_path.read_text())
            except:
                logs = []
        logs.append(entry)
        logs = logs[-1000:]  # keep last 1000
        self.log_path.write_text(json.dumps(logs, indent=2))
