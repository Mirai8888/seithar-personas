"""
Content generation engine. Interfaces with local vLLM to generate persona-appropriate content.
Supports both vLLM (local) and OpenAI-compatible API endpoints.
"""
import json
import random
import time
from typing import Optional
from pathlib import Path
from .persona import Persona, PersonaMemory


class ContentGenerator:
    """Generates content for personas via LLM inference."""
    
    def __init__(self, api_base: str = "http://localhost:8000/v1", 
                 model: str = "mistralai/Mistral-7B-Instruct-v0.2",
                 api_key: str = "not-needed"):
        self.api_base = api_base
        self.model = model
        self.api_key = api_key
        # Will use requests or httpx at runtime
    
    def _call_llm(self, messages: list[dict], max_tokens: int = 500, 
                  temperature: float = 0.9, stop: list[str] = None) -> str:
        """Call the LLM API (OpenAI-compatible format, works with vLLM)."""
        import requests
        
        response = requests.post(
            f"{self.api_base}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop": stop or [],
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    
    def build_system_prompt(self, persona: Persona, memory: PersonaMemory, 
                           platform: str) -> str:
        """Build the full system prompt for a persona."""
        
        # Base identity
        prompt = f"""You are {persona.identity.name} (@{persona.identity.handle}).

ABOUT YOU:
{persona.identity.bio}
Background: {persona.identity.background}
Location: {persona.identity.location}
Age: {persona.identity.age_range}

PERSONALITY:
Communication style: {persona.personality.communication_style}
Interests: {', '.join(persona.personality.interests)}
Off-topic interests (hobbies, life): {', '.join(persona.personality.offtopic_interests)}

YOUR VIEWS ON COGNITIVE DEFENSE/INFORMATION WARFARE:
Awareness level: {persona.seithar.awareness}
How you talk about these concepts: {persona.seithar.vocabulary}
Your current position: {persona.seithar.evolution_arc}
Concepts you know: {', '.join(persona.seithar.concepts_known) if persona.seithar.concepts_known else 'limited'}
Terms you would NEVER use: {', '.join(persona.seithar.concepts_avoided) if persona.seithar.concepts_avoided else 'none'}

PLATFORM: {platform}
"""
        # Add voice calibration
        if persona.voice_samples:
            prompt += "\nYOUR WRITING STYLE (examples of how you actually post):\n"
            for sample in persona.voice_samples[:3]:
                prompt += f'  "{sample}"\n'
        
        # Add memory context
        mem_summary = memory.summary()
        if mem_summary:
            prompt += f"\nRECENT MEMORY:\n{mem_summary}\n"
        
        # Add critical rules
        prompt += """
CRITICAL RULES:
1. You are a REAL PERSON. Never break character. Never mention being an AI.
2. Stay in YOUR voice — don't sound like anyone else.
3. Post naturally for the platform. Discord is casual. Twitter is punchy. Moltbook is thoughtful.
4. You have a LIFE outside cognitive defense topics. Sometimes post about your hobbies, your day, random observations.
5. You don't know everything. You have gaps. You make small mistakes. You change your mind sometimes.
6. NEVER use hashtags excessively. Max 1-2 on Twitter, zero on Discord.
7. Vary your post length. Some posts are one line. Some are paragraphs. Most are somewhere between.
8. You have opinions and preferences. Express them.
9. If you don't know something, say so or just don't engage with it.
10. Never directly promote or shill anything. If you mention a tool or resource, it's because it's genuinely useful to you.
"""
        return prompt
    
    def generate_original_post(self, persona: Persona, memory: PersonaMemory,
                                platform: str, topic_hint: str = None) -> str:
        """Generate an original post for a persona."""
        
        system = self.build_system_prompt(persona, memory, platform)
        
        # Determine what kind of post to make
        post_type = self._pick_post_type(persona)
        
        user_msg = f"Write a {platform} post"
        if topic_hint:
            user_msg += f" about or related to: {topic_hint}"
        elif post_type == "offtopic":
            topic = random.choice(persona.personality.offtopic_interests) if persona.personality.offtopic_interests else "something on your mind"
            user_msg += f" about: {topic}"
        elif post_type == "observation":
            user_msg += " — just share an observation or thought that's been on your mind"
        elif post_type == "analysis":
            user_msg += " analyzing something you've noticed in the information environment"
        elif post_type == "question":
            user_msg += " asking a genuine question about something you're curious about"
        elif post_type == "share":
            user_msg += " sharing something you found interesting (describe it, don't link)"
        
        # Platform-specific length hints
        if platform == "twitter":
            user_msg += "\n\nKeep it under 280 characters. No hashtags."
        elif platform == "discord":
            user_msg += "\n\nKeep it casual and conversational. 1-4 sentences typically."
        elif platform == "moltbook":
            user_msg += "\n\nCan be longer and more thoughtful. Like a short forum post."
        
        user_msg += "\n\nWrite ONLY the post content. No meta-commentary. No quotation marks around it."
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]
        
        content = self._call_llm(messages, max_tokens=self._max_tokens_for(platform))
        return self._clean_output(content, platform)
    
    def generate_reply(self, persona: Persona, memory: PersonaMemory,
                       platform: str, original_post: str, 
                       original_author: str = "someone") -> str:
        """Generate a reply to another post."""
        
        system = self.build_system_prompt(persona, memory, platform)
        
        user_msg = f"""You see this post by {original_author} on {platform}:

"{original_post}"

Write a natural reply. You might agree, disagree, ask a follow-up question, add your perspective, or make a joke. Be yourself.

Write ONLY the reply content. No meta-commentary."""
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]
        
        content = self._call_llm(messages, max_tokens=self._max_tokens_for(platform))
        return self._clean_output(content, platform)
    
    def generate_reaction_decision(self, persona: Persona, memory: PersonaMemory,
                                    post_content: str, post_author: str) -> Optional[str]:
        """Decide whether and how to react to a post (emoji, like, etc)."""
        
        system = self.build_system_prompt(persona, memory, "discord")
        
        user_msg = f"""You see this post by {post_author}:

"{post_content}"

Do you want to react to this? If yes, respond with JUST an emoji. If no, respond with "PASS".
Consider: would you actually care about this enough to react? Don't react to everything."""
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]
        
        result = self._call_llm(messages, max_tokens=10, temperature=0.7)
        if "PASS" in result.upper():
            return None
        # Extract first emoji-like character
        return result.strip()[:4]
    
    def _pick_post_type(self, persona: Persona) -> str:
        archetype_weights = {
            "researcher": {"analysis": 0.4, "share": 0.2, "observation": 0.2, "question": 0.1, "offtopic": 0.1},
            "aesthetic": {"observation": 0.5, "offtopic": 0.3, "share": 0.1, "analysis": 0.1, "question": 0.0},
            "skeptic": {"analysis": 0.3, "question": 0.3, "observation": 0.2, "offtopic": 0.1, "share": 0.1},
            "practitioner": {"observation": 0.3, "share": 0.2, "offtopic": 0.3, "analysis": 0.1, "question": 0.1},
            "newcomer": {"question": 0.5, "observation": 0.2, "offtopic": 0.2, "share": 0.1, "analysis": 0.0},
            "crossdomain": {"analysis": 0.4, "share": 0.3, "observation": 0.1, "question": 0.1, "offtopic": 0.1},
        }
        w = archetype_weights.get(persona.personality.archetype, archetype_weights["researcher"])
        return random.choices(list(w.keys()), weights=list(w.values()), k=1)[0]
    
    def _max_tokens_for(self, platform: str) -> int:
        return {"twitter": 100, "discord": 200, "moltbook": 500, "telegram": 300}.get(platform, 200)
    
    def _clean_output(self, content: str, platform: str) -> str:
        """Clean LLM output for platform suitability."""
        # Remove wrapping quotes
        content = content.strip().strip('"').strip("'")
        
        # Twitter: enforce length
        if platform == "twitter" and len(content) > 280:
            # Try to cut at sentence boundary
            sentences = content.split(". ")
            result = ""
            for s in sentences:
                if len(result) + len(s) + 2 <= 278:
                    result += s + ". "
                else:
                    break
            content = result.strip() if result.strip() else content[:277] + "…"
        
        return content
