#!/usr/bin/env python3
"""
Seithar Persona System — Main Orchestrator

Runs the persona network: generates content, manages schedules,
routes to platforms, and maintains safety guardrails.

Usage:
    python main.py run          # Start the orchestrator loop
    python main.py schedule     # Generate today's schedule and show it
    python main.py test <id>    # Generate a test post for a persona
    python main.py status       # Show system status
"""
import sys
import json
import time
import random
import logging
from pathlib import Path
from datetime import datetime, timezone

from core import (
    Persona, PersonaMemory, 
    Scheduler, PostingEvent,
    ContentGenerator,
    PlatformRouter, DiscordAdapter, MoltbookAdapter, TwitterAdapter, TelegramAdapter,
)
from core.safety_monitor import SafetyMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("orchestrator")

BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
PERSONAS_DIR = CONFIG_DIR / "personas"
PLATFORMS_CONFIG = CONFIG_DIR / "platforms.yaml"


def load_personas() -> list[Persona]:
    """Load all persona configs from config/personas/."""
    personas = []
    for path in sorted(PERSONAS_DIR.glob("*.json")):
        try:
            p = Persona.load_config(path)
            personas.append(p)
            logger.info(f"Loaded persona: {p.id} ({p.identity.name})")
        except Exception as e:
            logger.error(f"Failed to load {path.name}: {e}")
    return personas


def load_platform_config() -> dict:
    """Load platform credentials."""
    if PLATFORMS_CONFIG.exists():
        import yaml
        return yaml.safe_load(PLATFORMS_CONFIG.read_text())
    # Fallback: try JSON
    json_path = CONFIG_DIR / "platforms.json"
    if json_path.exists():
        return json.loads(json_path.read_text())
    return {}


def setup_router(personas: list[Persona], platform_config: dict) -> PlatformRouter:
    """Set up platform adapters for each persona."""
    router = PlatformRouter()
    
    for persona in personas:
        for pp in persona.platforms:
            if not pp.active:
                continue
            
            adapter = None
            creds_path = Path(pp.credentials_path) if pp.credentials_path else None
            
            if pp.platform == "discord" and creds_path and creds_path.exists():
                creds = json.loads(creds_path.read_text())
                adapter = DiscordAdapter(
                    token=creds["token"],
                    guild_id=creds.get("guild_id", "1444739404576067647"),
                    channel_ids=creds.get("channel_ids", {}),
                )
            elif pp.platform == "moltbook" and creds_path and creds_path.exists():
                creds = json.loads(creds_path.read_text())
                adapter = MoltbookAdapter(api_key=creds["api_key"])
            elif pp.platform == "twitter" and creds_path and creds_path.exists():
                adapter = TwitterAdapter(cookies_path=str(creds_path))
            elif pp.platform == "telegram" and creds_path and creds_path.exists():
                creds = json.loads(creds_path.read_text())
                adapter = TelegramAdapter(
                    bot_token=creds["bot_token"],
                    chat_ids=creds.get("chat_ids", {}),
                )
            
            if adapter:
                router.register(persona.id, pp.platform, adapter)
                logger.info(f"  Registered {persona.id} on {pp.platform}")
    
    return router


def execute_event(event: PostingEvent, persona: Persona, memory: PersonaMemory,
                  generator: ContentGenerator, router: PlatformRouter,
                  safety: SafetyMonitor) -> bool:
    """Execute a single posting event."""
    
    logger.info(f"Executing: {event}")
    
    # Generate content based on event type
    if event.event_type == "original" or event.event_type == "offtopic":
        topic = None
        if event.event_type == "offtopic" and persona.personality.offtopic_interests:
            topic = random.choice(persona.personality.offtopic_interests)
        content = generator.generate_original_post(persona, memory, event.platform, topic)
    
    elif event.event_type == "reply":
        # Get feed and pick something to reply to
        feed = router.get_feed(persona.id, event.platform, limit=10)
        if not feed:
            logger.info(f"  No feed items to reply to, converting to original post")
            content = generator.generate_original_post(persona, memory, event.platform)
        else:
            # Pick a post to reply to (prefer posts with fewer replies, or interesting content)
            target = random.choice(feed[:5])
            content = generator.generate_reply(
                persona, memory, event.platform,
                target.get("content", target.get("title", "")),
                target.get("author", "someone"),
            )
            event.context["reply_to"] = target.get("id")
            event.context["reply_to_author"] = target.get("author")
    
    elif event.event_type == "react":
        feed = router.get_feed(persona.id, event.platform, limit=10)
        if feed:
            target = random.choice(feed[:5])
            emoji = generator.generate_reaction_decision(
                persona, memory, 
                target.get("content", ""), target.get("author", "someone")
            )
            if emoji:
                result = router.adapters.get(persona.id, {}).get(event.platform)
                if result:
                    result.react(target["id"], emoji)
                    logger.info(f"  Reacted with {emoji} to {target.get('author')}")
                memory.add_post(event.platform, f"[reacted {emoji}]", {})
            return True
        return True
    else:
        content = generator.generate_original_post(persona, memory, event.platform)
    
    if not content:
        logger.warning(f"  No content generated for {event}")
        return False
    
    # Safety check
    is_safe, reason = safety.full_check(persona.id, event.platform, content)
    if not is_safe:
        logger.warning(f"  Safety block: {reason}")
        return False
    
    # Post it
    if event.context.get("reply_to"):
        result = router.reply(persona.id, event.platform, content, event.context["reply_to"])
    else:
        result = router.post(persona.id, event.platform, content)
    
    if result.get("success"):
        safety.record_post(persona.id, event.platform)
        memory.add_post(event.platform, content, result)
        logger.info(f"  Posted: {content[:80]}...")
        return True
    else:
        logger.error(f"  Post failed: {result.get('error', 'unknown')}")
        return False


def run_loop(personas: list[Persona], generator: ContentGenerator,
             router: PlatformRouter, safety: SafetyMonitor):
    """Main orchestrator loop."""
    
    memories = {p.id: PersonaMemory(p.id, DATA_DIR) for p in personas}
    scheduler = Scheduler(personas, DATA_DIR)
    
    logger.info("Generating daily schedule...")
    scheduler.generate_daily_schedule()
    logger.info(f"Scheduled {len(scheduler.queue)} events for today")
    
    for event in scheduler.queue:
        logger.info(f"  {event}")
    
    logger.info("Starting orchestrator loop...")
    
    while True:
        pending = scheduler.get_pending(window_seconds=60)
        
        for event in pending:
            persona = scheduler.personas.get(event.persona_id)
            if not persona:
                continue
            
            memory = memories.get(event.persona_id)
            if not memory:
                continue
            
            # Update mood before posting
            scheduler.update_mood(persona, memory)
            
            # Add human-like delay (don't execute exactly on schedule)
            delay = random.uniform(5, 120)
            time.sleep(delay)
            
            success = execute_event(event, persona, memory, generator, router, safety)
            scheduler.mark_executed(event)
            
            if success:
                # Random delay between personas to avoid coordination tells
                time.sleep(random.uniform(30, 180))
        
        # Check if we need to generate tomorrow's schedule
        now = datetime.now(timezone.utc)
        if now.hour == 23 and now.minute > 50 and not any(
            not e.executed for e in scheduler.queue
        ):
            logger.info("Generating schedule for tomorrow...")
            scheduler.queue.clear()
            scheduler.generate_daily_schedule(now + __import__("datetime").timedelta(days=1))
        
        # Save state periodically
        scheduler.save_state()
        for m in memories.values():
            m.save()
        
        # Sleep before checking again
        time.sleep(30)


def cmd_run():
    personas = load_personas()
    if not personas:
        logger.error("No personas loaded! Add configs to config/personas/")
        sys.exit(1)
    
    platform_config = load_platform_config()
    
    # Initialize components
    generator = ContentGenerator(
        api_base=platform_config.get("llm", {}).get("api_base", "http://localhost:8000/v1"),
        model=platform_config.get("llm", {}).get("model", "mistralai/Mistral-7B-Instruct-v0.2"),
    )
    router = setup_router(personas, platform_config)
    safety = SafetyMonitor(DATA_DIR)
    
    run_loop(personas, generator, router, safety)


def cmd_schedule():
    personas = load_personas()
    scheduler = Scheduler(personas, DATA_DIR)
    scheduler.generate_daily_schedule()
    
    print(f"\n{'='*60}")
    print(f"  DAILY SCHEDULE — {datetime.now().strftime('%Y-%m-%d')}")
    print(f"  {len(scheduler.queue)} events for {len(personas)} personas")
    print(f"{'='*60}\n")
    
    for event in scheduler.queue:
        dt = datetime.fromtimestamp(event.scheduled_time)
        print(f"  {dt.strftime('%H:%M')}  {event.persona_id:<20} {event.platform:<10} {event.event_type}")


def cmd_test(persona_id: str):
    personas = load_personas()
    persona = next((p for p in personas if p.id == persona_id), None)
    if not persona:
        print(f"Unknown persona: {persona_id}")
        print(f"Available: {', '.join(p.id for p in personas)}")
        sys.exit(1)
    
    platform_config = load_platform_config()
    generator = ContentGenerator(
        api_base=platform_config.get("llm", {}).get("api_base", "http://localhost:8000/v1"),
        model=platform_config.get("llm", {}).get("model", "mistralai/Mistral-7B-Instruct-v0.2"),
    )
    memory = PersonaMemory(persona.id, DATA_DIR)
    
    platform = persona.platforms[0].platform if persona.platforms else "discord"
    
    print(f"\nGenerating test post for {persona.identity.name} (@{persona.identity.handle})...")
    print(f"Platform: {platform}")
    print(f"Archetype: {persona.personality.archetype}")
    print(f"Seithar awareness: {persona.seithar.awareness}")
    print(f"\n{'─'*40}\n")
    
    content = generator.generate_original_post(persona, memory, platform)
    print(content)
    print(f"\n{'─'*40}")


def cmd_status():
    personas = load_personas()
    print(f"\n{'='*60}")
    print(f"  SEITHAR PERSONA SYSTEM STATUS")
    print(f"{'='*60}\n")
    print(f"  Personas loaded: {len(personas)}")
    
    for p in personas:
        memory = PersonaMemory(p.id, DATA_DIR)
        platforms = ", ".join(pp.platform for pp in p.platforms if pp.active)
        post_count = len(memory.posts)
        print(f"  {p.id:<20} {p.identity.name:<25} [{platforms}] posts={post_count}")
    
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "run":
        cmd_run()
    elif cmd == "schedule":
        cmd_schedule()
    elif cmd == "test":
        if len(sys.argv) < 3:
            print("Usage: python main.py test <persona_id>")
            sys.exit(1)
        cmd_test(sys.argv[2])
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
