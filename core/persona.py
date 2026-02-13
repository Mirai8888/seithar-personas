"""
Persona data model and state management.
Each persona is a fully realized human identity with memory, personality, and platform presence.
"""
import json
import time
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

ARCHETYPES = ["researcher", "aesthetic", "skeptic", "practitioner", "newcomer", "crossdomain"]

@dataclass
class PersonaIdentity:
    name: str
    handle: str
    bio: str
    avatar_desc: str
    background: str
    location: str
    age_range: str  # e.g. "28-34"
    gender: str
    languages: list[str] = field(default_factory=lambda: ["en"])

@dataclass 
class PersonaPersonality:
    archetype: str
    openness: int        # 0-100
    conscientiousness: int
    extraversion: int
    agreeableness: int
    neuroticism: int
    communication_style: str  # e.g. "clinical_terse", "poetic_fragmented", "casual_curious"
    interests: list[str] = field(default_factory=list)
    offtopic_interests: list[str] = field(default_factory=list)  # non-seithar hobbies

@dataclass
class SeitharRelationship:
    awareness: str       # "explicit", "discovering", "independent", "skeptical", "unaware"
    vocabulary: str      # "sct_codes", "academic", "intuitive", "different_terms", "none"
    evolution_phase: int # 0=initial, 1=curious, 2=engaged, 3=advocate, 4=integrated
    evolution_arc: str   # description of how position changes over time
    concepts_known: list[str] = field(default_factory=list)
    concepts_avoided: list[str] = field(default_factory=list)  # terms this persona would never use

@dataclass
class PlatformPresence:
    platform: str        # "discord", "twitter", "telegram", "moltbook"
    handle: str
    credentials_path: str
    active: bool = True
    joined_date: Optional[str] = None

@dataclass
class PostingSchedule:
    active_hours: tuple[int, int] = (9, 22)  # UTC hours
    posts_per_day: tuple[float, float] = (1.0, 3.0)  # min, max
    active_days: list[int] = field(default_factory=lambda: [0,1,2,3,4,5,6])  # 0=Mon
    jitter_minutes: int = 45  # random offset per scheduled post
    burst_probability: float = 0.1  # chance of posting 2-3 times quickly
    quiet_day_probability: float = 0.15  # chance of not posting at all

@dataclass
class Persona:
    id: str
    identity: PersonaIdentity
    personality: PersonaPersonality
    seithar: SeitharRelationship
    platforms: list[PlatformPresence]
    schedule: PostingSchedule
    voice_samples: list[str] = field(default_factory=list)
    system_prompt: str = ""
    
    # Runtime state (not saved to config, loaded from memory)
    last_post_time: float = 0
    post_count: int = 0
    mood: float = 0.5  # 0=withdrawn, 1=energetic
    
    def save_config(self, config_dir: Path):
        """Save persona configuration (not runtime state)."""
        data = {
            "id": self.id,
            "identity": asdict(self.identity),
            "personality": asdict(self.personality),
            "seithar": asdict(self.seithar),
            "platforms": [asdict(p) for p in self.platforms],
            "schedule": asdict(self.schedule),
            "voice_samples": self.voice_samples,
            "system_prompt": self.system_prompt,
        }
        path = config_dir / f"{self.id}.json"
        path.write_text(json.dumps(data, indent=2))
    
    @classmethod
    def load_config(cls, path: Path) -> "Persona":
        data = json.loads(path.read_text())
        return cls(
            id=data["id"],
            identity=PersonaIdentity(**data["identity"]),
            personality=PersonaPersonality(**data["personality"]),
            seithar=SeitharRelationship(**data["seithar"]),
            platforms=[PlatformPresence(**p) for p in data["platforms"]],
            schedule=PostingSchedule(**data["schedule"]),
            voice_samples=data.get("voice_samples", []),
            system_prompt=data.get("system_prompt", ""),
        )


class PersonaMemory:
    """Per-persona memory bank. Stores conversation history, posted content, and learned context."""
    
    def __init__(self, persona_id: str, data_dir: Path):
        self.persona_id = persona_id
        self.path = data_dir / "memory" / f"{persona_id}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._load()
    
    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text())
        else:
            data = {}
        self.posts = data.get("posts", [])           # list of {platform, content, timestamp, engagement}
        self.interactions = data.get("interactions", [])  # list of {with_persona, platform, content, timestamp}
        self.discoveries = data.get("discoveries", [])    # concepts/people "discovered"
        self.mood_history = data.get("mood_history", [])
        self.notes = data.get("notes", [])            # internal persona "thoughts"
    
    def save(self):
        data = {
            "posts": self.posts[-200:],  # keep last 200
            "interactions": self.interactions[-100:],
            "discoveries": self.discoveries,
            "mood_history": self.mood_history[-50:],
            "notes": self.notes[-50:],
        }
        self.path.write_text(json.dumps(data, indent=2))
    
    def add_post(self, platform: str, content: str, engagement: dict = None):
        self.posts.append({
            "platform": platform,
            "content": content,
            "timestamp": time.time(),
            "engagement": engagement or {},
        })
        self.save()
    
    def add_interaction(self, with_persona: str, platform: str, content: str):
        self.interactions.append({
            "with_persona": with_persona,
            "platform": platform, 
            "content": content,
            "timestamp": time.time(),
        })
        self.save()
    
    def add_discovery(self, concept: str, source: str):
        self.discoveries.append({
            "concept": concept,
            "source": source,
            "timestamp": time.time(),
        })
        self.save()
    
    def recent_posts(self, n: int = 10, platform: str = None) -> list[dict]:
        posts = self.posts
        if platform:
            posts = [p for p in posts if p["platform"] == platform]
        return posts[-n:]
    
    def summary(self, max_chars: int = 500) -> str:
        """Generate a brief memory summary for inclusion in prompts."""
        lines = []
        recent = self.recent_posts(5)
        if recent:
            lines.append(f"Recent posts ({len(recent)}):")
            for p in recent[-3:]:
                snippet = p["content"][:80] + "..." if len(p["content"]) > 80 else p["content"]
                lines.append(f"  [{p['platform']}] {snippet}")
        if self.discoveries:
            lines.append(f"Discoveries: {', '.join(d['concept'] for d in self.discoveries[-5:])}")
        return "\n".join(lines)[:max_chars]
