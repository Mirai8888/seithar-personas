"""
Scheduling engine for persona activity.
Generates human-like posting schedules with jitter, mood variation, and realistic patterns.
"""
import time
import random
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from .persona import Persona, PersonaMemory


class PostingEvent:
    """A scheduled posting event."""
    def __init__(self, persona_id: str, platform: str, event_type: str, 
                 scheduled_time: float, context: dict = None):
        self.persona_id = persona_id
        self.platform = platform
        self.event_type = event_type  # "original", "reply", "react", "offtopic"
        self.scheduled_time = scheduled_time
        self.context = context or {}
        self.executed = False
    
    def __repr__(self):
        dt = datetime.fromtimestamp(self.scheduled_time, tz=timezone.utc)
        return f"<Event {self.persona_id}@{self.platform} {self.event_type} at {dt.strftime('%H:%M')}>"


class Scheduler:
    """Generates and manages posting schedules for all personas."""
    
    def __init__(self, personas: list[Persona], data_dir: Path):
        self.personas = {p.id: p for p in personas}
        self.data_dir = data_dir
        self.queue: list[PostingEvent] = []
        self.state_path = data_dir / "events" / "scheduler_state.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
    
    def generate_daily_schedule(self, date: datetime = None):
        """Generate all posting events for a given day."""
        if date is None:
            date = datetime.now(timezone.utc)
        
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for persona in self.personas.values():
            sched = persona.schedule
            
            # Check if today is an active day
            if day_start.weekday() not in sched.active_days:
                continue
            
            # Quiet day check — some days the persona just doesn't post
            if random.random() < sched.quiet_day_probability:
                continue
            
            # Determine number of posts today
            base_posts = random.uniform(*sched.posts_per_day)
            
            # Mood adjustment: higher mood = more posts
            mood_factor = 0.7 + (persona.mood * 0.6)  # 0.7 to 1.3
            num_posts = max(1, round(base_posts * mood_factor))
            
            # Burst mode: occasionally post 2-3 times in quick succession
            is_burst = random.random() < sched.burst_probability
            if is_burst:
                num_posts = min(num_posts + random.randint(1, 2), 5)
            
            # Generate posting times within active hours
            active_start = sched.active_hours[0]
            active_end = sched.active_hours[1]
            
            # Distribute posts across the active window
            for i in range(num_posts):
                if is_burst and i > 0:
                    # Burst posts happen 5-30 min after the first
                    base_time = self.queue[-1].scheduled_time if self.queue else time.time()
                    post_time = base_time + random.randint(300, 1800)
                else:
                    # Normal distribution across active hours
                    hour = random.uniform(active_start, active_end)
                    minute = random.randint(0, 59)
                    second = random.randint(0, 59)
                    
                    post_dt = day_start.replace(
                        hour=int(hour), 
                        minute=minute, 
                        second=second
                    )
                    # Add jitter
                    jitter = random.randint(-sched.jitter_minutes * 60, sched.jitter_minutes * 60)
                    post_time = post_dt.timestamp() + jitter
                
                # Determine event type
                event_type = self._pick_event_type(persona)
                
                # Pick platform
                active_platforms = [p for p in persona.platforms if p.active]
                if not active_platforms:
                    continue
                platform = random.choice(active_platforms)
                
                event = PostingEvent(
                    persona_id=persona.id,
                    platform=platform.platform,
                    event_type=event_type,
                    scheduled_time=post_time,
                )
                self.queue.append(event)
        
        # Sort queue by time
        self.queue.sort(key=lambda e: e.scheduled_time)
    
    def _pick_event_type(self, persona: Persona) -> str:
        """Pick what type of post this persona makes, weighted by archetype."""
        weights = {
            "researcher": {"original": 0.5, "reply": 0.3, "react": 0.1, "offtopic": 0.1},
            "aesthetic": {"original": 0.6, "reply": 0.1, "react": 0.2, "offtopic": 0.1},
            "skeptic": {"original": 0.3, "reply": 0.5, "react": 0.1, "offtopic": 0.1},
            "practitioner": {"original": 0.4, "reply": 0.3, "react": 0.1, "offtopic": 0.2},
            "newcomer": {"original": 0.2, "reply": 0.4, "react": 0.2, "offtopic": 0.2},
            "crossdomain": {"original": 0.5, "reply": 0.3, "react": 0.1, "offtopic": 0.1},
        }
        
        archetype = persona.personality.archetype
        w = weights.get(archetype, weights["researcher"])
        types = list(w.keys())
        probs = list(w.values())
        return random.choices(types, weights=probs, k=1)[0]
    
    def get_pending(self, window_seconds: int = 300) -> list[PostingEvent]:
        """Get events that should be executed now (within window)."""
        now = time.time()
        pending = []
        for event in self.queue:
            if event.executed:
                continue
            if event.scheduled_time <= now + window_seconds:
                pending.append(event)
            elif event.scheduled_time > now + window_seconds:
                break  # queue is sorted, no need to check further
        return pending
    
    def mark_executed(self, event: PostingEvent):
        event.executed = True
    
    def update_mood(self, persona: Persona, memory: PersonaMemory):
        """Update persona mood based on recent engagement and time patterns."""
        # Base mood drift toward 0.5
        persona.mood += (0.5 - persona.mood) * 0.1
        
        # Engagement boost
        recent = memory.recent_posts(5)
        if recent:
            avg_engagement = sum(
                p.get("engagement", {}).get("likes", 0) + p.get("engagement", {}).get("replies", 0)
                for p in recent
            ) / len(recent)
            if avg_engagement > 5:
                persona.mood = min(1.0, persona.mood + 0.1)
        
        # Time-of-day personality: introverts fade in evening
        hour = datetime.now().hour
        if persona.personality.extraversion < 40 and (hour > 22 or hour < 8):
            persona.mood = max(0.1, persona.mood - 0.15)
        
        # Random fluctuation
        persona.mood += random.uniform(-0.05, 0.05)
        persona.mood = max(0.0, min(1.0, persona.mood))
    
    def save_state(self):
        state = {
            "queue": [
                {
                    "persona_id": e.persona_id,
                    "platform": e.platform,
                    "event_type": e.event_type,
                    "scheduled_time": e.scheduled_time,
                    "executed": e.executed,
                    "context": e.context,
                }
                for e in self.queue if not e.executed
            ],
            "updated": time.time(),
        }
        self.state_path.write_text(json.dumps(state, indent=2))
