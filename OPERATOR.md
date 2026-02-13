# OPERATOR MANUAL

everything you need to run the persona network. no fluff.

## where things are

```
~/seithar-personas/              <- the repo (on github, no creds)
~/.openclaw/workspace/personas/  <- live persona configs (not on github)
~/.config/personas/              <- account credentials (not on github)
/tmp/persona-logs/               <- runtime logs
```

credentials are NEVER on github. only the engine code and templates.

## quick start

```bash
# see who's running
cd ~/.openclaw/workspace/personas
bash launch.sh status

# start a persona
bash launch.sh rin
bash launch.sh sorath

# start all personas
bash launch.sh all

# stop one
bash launch.sh stopone rin

# stop everything
bash launch.sh stop

# check logs
tail -f /tmp/persona-logs/rin.log
tail -f /tmp/persona-logs/sorath.log
```

## adding a new persona (2 minutes)

### 1. save the discord account credentials

```bash
cat > ~/.config/personas/NEW-ACCOUNT.json << 'EOF'
{
  "token": "DISCORD_USER_TOKEN_HERE",
  "email": "account@email.com",
  "password": "password123"
}
EOF
chmod 600 ~/.config/personas/NEW-ACCOUNT.json
```

### 2. create the persona config

```bash
mkdir -p ~/.openclaw/workspace/personas/NAMEHERE
cp ~/.openclaw/workspace/personas/TEMPLATE.json ~/.openclaw/workspace/personas/NAMEHERE/persona.json
```

then edit `persona.json`:
- change `"name"` to the persona name
- change `"token_file"` to point at the credentials file
- write the `"system_prompt"` describing personality
- adjust `"reactions"`, `"interest_keywords"`, timing values
- add `"invites": ["https://discord.gg/INVITE1", "https://discord.gg/INVITE2"]` to auto-join servers on startup

### 3. set up the discord profile

the intern (me) handles this: avatar, display name, bio, joining servers.
or do it manually by logging into discord with the account.

### 4. launch

```bash
cd ~/.openclaw/workspace/personas
bash launch.sh NAMEHERE
```

check it's working:
```bash
tail -f /tmp/persona-logs/NAMEHERE.log
```

## current personas

| name | type | status | servers |
|------|------|--------|---------|
| rin | egirl, infosec, flirty | RUNNING | seithar, milady village |
| sorath | theory, esoteric, terse | RUNNING | seithar |

## how it works

- each persona runs as a separate python process
- uses discord.py-self (selfbot library, appears as normal user)
- LLM responses via groq API (free, llama-3.3-70b-versatile)
- groq API key is at `~/.config/fleshengine/credentials.json`
- rolling 20-message context window per channel
- human-like typing delays (2-10 seconds)
- cooldown between unprompted messages (2-3 minutes)
- reacts to messages with configurable probability
- higher engagement in external servers to build presence

## switching to local models

edit the persona's `persona.json`, change voice section:

```json
"voice": {
    "model": "mistral",
    "api_base": "http://localhost:11434/v1",
    "temperature": 0.9,
    "system_prompt": "..."
}
```

then restart. but groq free tier is better quality and basically unlimited.

## the repo

`github.com/Mirai8888/seithar-personas`

contains: engine code, launcher, templates, examples.
does NOT contain: tokens, passwords, API keys, live persona configs.

## if something breaks

```bash
# check if process is alive
bash launch.sh status

# check for errors
tail -50 /tmp/persona-logs/NAMEHERE.log

# kill and restart
bash launch.sh stopone NAMEHERE
bash launch.sh NAMEHERE

# nuclear option
bash launch.sh stop
bash launch.sh all
```

## all seithar tools (quick reference)

| tool | location | what it does |
|------|----------|-------------|
| persona engine | ~/seithar-personas/ | discord selfbot personas |
| fleshengine | ~/fleshengine/ | cognitive profiling platform (live at fleshengine.com) |
| holespawn | ~/HoleSpawn/ | offensive profiling + SCT mapping |
| cogdef scanner | ~/seithar-cogdef/ | defensive SCT scanner (live at seithar.com/scanner) |
| threatmouth | ~/ThreatMouth/ | threat intel discord bot |
| seithar site | ~/seithar-site/ | seithar.com source |
| research | ~/seithar-research/ | all papers, analyses, output |
| content forge | ~/seithar-research/tools/content-forge.py | batch content generation |
| seidr engine | ~/seithar-research/tools/seidr-engine.py | narrative seeding pipeline |

all repos are at github.com/Mirai8888/
