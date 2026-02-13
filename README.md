# seithar-personas

generic discord persona engine. one orchestrator, infinite voices.

## what it does

runs discord selfbot personas powered by LLM inference (groq/llama-3.3-70b). each persona is a JSON config defining voice, behavior, and channel rules. the engine handles human-like timing, context tracking, reaction patterns, and rate limiting.

## setup

```
pip install discord.py-self requests
```

credentials go in `~/.config/personas/<name>.json`:
```json
{"token": "discord-user-token", "email": "...", "password": "..."}
```

groq API key in `~/.config/fleshengine/credentials.json`:
```json
{"groq_api_key": "gsk_..."}
```

## usage

```bash
# create persona
mkdir -p personas/yourpersona
cp TEMPLATE.json personas/yourpersona/persona.json
# edit persona.json with voice, behavior, channels

# launch
python3 engine.py --persona yourpersona

# or use the launcher
bash launch.sh yourpersona     # one
bash launch.sh all             # all
bash launch.sh stop            # kill all
bash launch.sh status          # who's running
```

## persona config

see `TEMPLATE.json` for full schema. key sections:

- **channels**: active (respond), lurk (react only), ignore
- **behavior**: react probability, response cooldown, typing delays, interest keywords
- **voice**: LLM system prompt defining personality, model, temperature

## architecture

```
engine.py          — generic orchestrator (one instance per persona)
launch.sh          — process manager
TEMPLATE.json      — blank persona config
examples/          — example configs
personas/<name>/   — per-persona configs (gitignored)
```

each persona runs as a separate process. no shared state. crash one, others keep running.

## design principles

- personas must pass as human. timing, reactions, message length all tuned for plausibility
- rolling context window (20 messages) per channel for conversational coherence
- cooldown system prevents flooding. direct mentions bypass cooldown
- interest keywords trigger higher response probability on relevant topics
- reactions are independent of responses (can react without responding)

---

seithar group research division | 認知作戦 | seithar.com
