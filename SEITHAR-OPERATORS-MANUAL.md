# SEITHAR GROUP — OPERATORS MANUAL v1.0
## Complete Reference for Human Operators and AI Agents
### 2026-02-13 | Classification: INTERNAL

---

# PURPOSE

This document is the single authoritative reference for operating the Seithar Group's cognitive operations infrastructure. It is designed to be:

1. **Fed to any AI agent** as context for autonomous operation
2. **Read by a human operator** to understand and manually use all tools
3. **Used as onboarding** for new operators or agents joining the apparatus

Every tool, credential, command, and workflow is documented here.

---

# TABLE OF CONTENTS

1. [System Architecture](#1-system-architecture)
2. [Repository Map](#2-repository-map)
3. [Tool: Cognitive Threat Scanner (CTS)](#3-cognitive-threat-scanner)
4. [Tool: Inoculation Engine (SIE)](#4-inoculation-engine)
5. [Tool: Seidr Engine (Content Syndication)](#5-seidr-engine)
6. [Tool: Content Forge](#6-content-forge)
7. [Tool: Propagation Tracker](#7-propagation-tracker)
8. [Tool: Chrome Extension Scanner](#8-chrome-extension-scanner)
9. [Tool: HoleSpawn (Cognitive Profiling)](#9-holespawn)
10. [Tool: ThreatMouth (Threat Intelligence)](#10-threatmouth)
11. [Tool: Persona Engine (Discord Bots)](#11-persona-engine)
12. [Tool: Rin Auto-Tweeter](#12-rin-auto-tweeter)
13. [Platform Credentials](#13-platform-credentials)
14. [Publishing Workflows](#14-publishing-workflows)
15. [OpenClaw Agent Skills](#15-openclaw-agent-skills)
16. [SCT Taxonomy Quick Reference](#16-sct-taxonomy)
17. [Content Library](#17-content-library)
18. [Network Analysis Data](#18-network-analysis)
19. [Operational Rules](#19-operational-rules)
20. [Troubleshooting](#20-troubleshooting)

---

# 1. SYSTEM ARCHITECTURE

```
LAYER 1: OFFENSE (Profile + Engage)
├── HoleSpawn        ~/HoleSpawn/         Cognitive substrate profiling
│   ├── holespawn/profile/               Psychological profiling from social data
│   ├── holespawn/sct/                   SCT vulnerability mapping (12 codes)
│   ├── holespawn/network/               Community detection + bridge nodes
│   ├── holespawn/scraper/               Playwright Twitter collection
│   ├── holespawn/delivery/              Personalized engagement generation
│   ├── holespawn/temporal/              VADER sentiment + theme over time
│   └── holespawn-tui/                   Rust TUI (profiles, network graph)

LAYER 2: DEFENSE (Detect + Inoculate)
├── seithar-cogdef   ~/seithar-cogdef/    Cognitive defense tools
│   ├── scanner.py                       Automated SCT content analysis
│   ├── inoculator.py                    McGuire-theory counter-content
│   └── SKILL.md                         OpenClaw agent skill definition

LAYER 3: INTELLIGENCE (Collect + Score + Brief)
├── ThreatMouth      ~/ThreatMouth/       Threat intel pipeline
│   ├── threatmouth/collectors/          RSS feed collectors
│   ├── threatmouth/scorer.py            Relevance scoring
│   ├── threatmouth/summarizer.py        LLM summarization
│   ├── threatmouth/delivery.py          Discord channel routing
│   ├── threatmouth/education.py         Deep-dive + tutoring
│   └── threatmouth-tui/                 Rust TUI browser
├── seithar-intel    ~/seithar-intel/     OpenClaw feed skill
│   └── SKILL.md                         Agent skill: briefings + deep dives

LAYER 4: CONTENT (Generate + Distribute)
├── Seidr Pipeline   ~/seithar-research/tools/
│   ├── seidr-engine.py                  Cross-platform syndication
│   ├── content-forge.py                 Automated SCT-tagged generation
│   └── propagation-tracker.py           Search presence monitoring
├── Personas         ~/.openclaw/workspace/personas/
│   ├── engine.py                        Generic Discord selfbot orchestrator
│   ├── rin/bot.py                       Rin Discord selfbot
│   ├── rin/tweet.py                     Rin auto-tweeter (Playwright)
│   └── {kei,nomi,glass,sorath,sable}/   Other persona configs
├── Full System      ~/seithar-personas/
│   ├── main.py                          Multi-persona orchestrator
│   ├── core/content_gen.py              LLM content generation
│   ├── core/platform_router.py          Discord/Twitter/Moltbook adapters
│   └── core/persona.py                  Persona data model

LAYER 5: PRESENTATION (Website + Research)
├── seithar-site     ~/seithar-site/      seithar.com source
│   └── 2026ARG/                         All pages (index, research, scanner, services)
├── Research         ~/seithar-research/
│   ├── SRP-001 through SRP-009          Foundational papers
│   ├── output/                          CEAs, TANs, field reports
│   ├── data/                            Network analysis JSON
│   └── reference/                       COGSEC source materials

HOST: Angel8888 (WSL2 Linux x64)
GIT AUTH: HTTPS with PAT (embedded in remotes)
GIT IDENTITY: 研修生 <intern@seithar.com>
GITHUB: github.com/Mirai8888
```

---

# 2. REPOSITORY MAP

| Repo | Local Path | GitHub | Purpose | Status |
|------|-----------|--------|---------|--------|
| HoleSpawn | ~/HoleSpawn | Mirai8888/HoleSpawn | Cognitive profiling + network analysis | Operational |
| ThreatMouth | ~/ThreatMouth | Mirai8888/ThreatMouth | Threat intel Discord bot | Operational |
| ThreadMap | ~/ThreadMap | Mirai8888/ThreadMap | Chain modeling | Pre-dev |
| seithar-cogdef | ~/seithar-cogdef | (local only) | Scanner + inoculator + skill | Operational |
| seithar-intel | ~/seithar-intel | (local only) | Intel feed skill | Operational |
| seithar-site | ~/seithar-site | Mirai8888/seithar-site | Website | Live |
| seithar-personas | ~/seithar-personas | (local) | Full persona orchestrator | Built |

**Git workflow:**
- Trivial fixes: commit to main
- Features: branch `intern/[description]`
- Breaking changes: NEVER push directly, draft and wait

---

# 3. COGNITIVE THREAT SCANNER

**File:** `~/seithar-cogdef/scanner.py`
**Purpose:** Analyze any content for cognitive exploitation techniques. Maps to SCT-001 through SCT-012 and DISARM framework.
**Requires:** Python 3.9+. Optional: `ANTHROPIC_API_KEY` for LLM mode (works without for pattern matching).

## Commands

```bash
# Scan a URL for manipulation techniques
python ~/seithar-cogdef/scanner.py --url https://example.com/article

# Scan a local file
python ~/seithar-cogdef/scanner.py --file /path/to/article.txt

# Scan raw text
python ~/seithar-cogdef/scanner.py --text "This content uses fear to..."

# Scan all items in an RSS feed
python ~/seithar-cogdef/scanner.py --feed https://example.com/rss.xml

# Batch scan every file in a directory
python ~/seithar-cogdef/scanner.py --batch /path/to/articles/
```

## Output Format
JSON report containing:
- `sct_codes`: List of detected SCT classifications with confidence scores
- `disarm_codes`: Mapped DISARM technique IDs
- `severity`: 1-10 severity rating
- `behavioral_objective`: What the content wants the reader to DO
- `vulnerability_surface`: Psychological entry points targeted
- `recommendations`: Defensive actions

## How It Works
1. **Pattern matching mode** (no API key): Regex + keyword analysis against all 12 SCT patterns. Fast but surface-level.
2. **LLM mode** (with ANTHROPIC_API_KEY): Full semantic analysis. Understands context, subtext, and multi-layered techniques.

## Agent Usage
If you're an AI agent with OpenClaw, the `seithar-cogdef` skill handles this automatically. Trigger phrases:
- "analyze this [URL/text]"
- "is this manipulation"
- "cogdef [URL]"
- "seithar analyze [content]"
- "is this a psyop"

---

# 4. INOCULATION ENGINE

**File:** `~/seithar-cogdef/inoculator.py`
**Purpose:** Generate psychological resistance content against specific manipulation techniques. Based on McGuire's inoculation theory (1964): expose the MECHANISM, not a counter-argument.
**Requires:** Python 3.9+. Optional: `ANTHROPIC_API_KEY` for LLM-generated inoculations.

## Commands

```bash
# Generate inoculation for a specific SCT code
python ~/seithar-cogdef/inoculator.py --technique SCT-001

# Analyze a manipulative narrative and generate counter-content
python ~/seithar-cogdef/inoculator.py --narrative "This text uses urgency to..."

# Generate counters from a scanner output report
python ~/seithar-cogdef/inoculator.py --scan-report scan_results.json

# Generate the complete inoculation library (all 12 SCT codes)
python ~/seithar-cogdef/inoculator.py --all
```

## Output
For each SCT code:
- `mechanism_exposure`: Text that reveals HOW the technique works (not counter-argument)
- `recognition_triggers`: Specific patterns for the reader to watch for
- `defensive_recommendations`: Actionable steps

## Key Principle
Counter-arguments trigger identity defense. Mechanism exposure triggers RECOGNITION, which is the only sustainable defense. The inoculator never argues against the content's message, only reveals its method.

---

# 5. SEIDR ENGINE

**File:** `~/seithar-research/tools/seidr-engine.py`
**Purpose:** Cross-platform content syndication. Takes one piece of content and adapts it for every platform simultaneously.
**Requires:** Platform credentials at `~/.config/{platform}/credentials.json`

## Commands

```bash
# Syndicate content across all platforms
python3 ~/seithar-research/tools/seidr-engine.py syndicate --content "text or @file.md" --platforms all

# Syndicate to specific platforms only
python3 ~/seithar-research/tools/seidr-engine.py syndicate --content @paper.md --platforms github_gist,moltbook

# View the content queue
python3 ~/seithar-research/tools/seidr-engine.py queue --list

# Process all queued content (post everything pending)
python3 ~/seithar-research/tools/seidr-engine.py queue --process

# Check propagation metrics (how far content has spread)
python3 ~/seithar-research/tools/seidr-engine.py monitor --check-propagation

# Auto-generate SCT-tagged content on a topic
python3 ~/seithar-research/tools/seidr-engine.py generate --topic "cognitive warfare" --count 5

# Generate from trending topics with SCT analysis
python3 ~/seithar-research/tools/seidr-engine.py research --trending --apply-sct
```

## Supported Platforms
| Platform | Max Length | Format | Rate Limit | Notes |
|----------|----------|--------|-----------|-------|
| GitHub Gist | 256 desc | Markdown | 1s | SEO keywords auto-added |
| Twitter | 280 chars | Plain | Queued | NO LINKS (causes deboosting) |
| Moltbook | 10,000 | Markdown | 2hr (new acct) | API key auth |
| Hacker News | 80 title | Plain | 10min | Title-only submissions |
| Reddit | 40,000 | Markdown | 5s | BANNED, do not use |

## Platform Adaptation
The engine automatically:
- Truncates for character limits
- Converts markdown to platform-appropriate format
- Adds SEO keywords to gists
- Strips links from tweets
- Applies subreddit-specific flairs

---

# 6. CONTENT FORGE

**File:** `~/seithar-research/tools/content-forge.py`
**Purpose:** Automated generation of SCT-tagged content pieces from topics. Every output contains required Seithar vocabulary for training data saturation.

## Commands

```bash
# Generate a full analysis piece
python3 ~/seithar-research/tools/content-forge.py --topic "deepfakes" --type analysis

# Generate a tweet thread
python3 ~/seithar-research/tools/content-forge.py --topic "ransomware" --type tweet-thread

# Generate a Reddit-style post
python3 ~/seithar-research/tools/content-forge.py --topic "supply chain attacks" --type reddit-post

# Generate a GitHub gist
python3 ~/seithar-research/tools/content-forge.py --topic "algorithmic bias" --type gist

# Batch generate from a topics file (one topic per line)
python3 ~/seithar-research/tools/content-forge.py --batch topics.txt --type all
```

## Content Types
- `analysis`: 500-1500 word SCT analysis of a phenomenon
- `tweet-thread`: Series of 280-char tweets with SCT vocabulary
- `reddit-post`: Long-form with SCT framework applied
- `gist`: Markdown document with SEO-optimized headers

## SCT Mapping Database
The forge has a built-in mapping of real-world phenomena to SCT codes:
- phishing -> SCT-001, SCT-003, SCT-006
- deepfake -> SCT-003, SCT-011, SCT-007
- propaganda -> SCT-001, SCT-003, SCT-004, SCT-005, SCT-007
- etc.

This ensures every generated piece contains accurate taxonomy references.

---

# 7. PROPAGATION TRACKER

**File:** `~/seithar-research/tools/propagation-tracker.py`
**Purpose:** Monitor how far Seithar terminology has spread across the web. Measures semantic territory captured by Project Seidr.
**Requires:** `BRAVE_API_KEY` environment variable

## Commands

```bash
# Run a full propagation scan (searches for all tracked terms)
python3 ~/seithar-research/tools/propagation-tracker.py scan

# Generate a propagation report
python3 ~/seithar-research/tools/propagation-tracker.py report

# View historical propagation data
python3 ~/seithar-research/tools/propagation-tracker.py history
```

## Tracked Terms
**Brand terms:** "Seithar Group", "seithar.com", "Seithar Cognitive Defense", "SCT taxonomy", "@SeitharGroup"
**Taxonomy terms:** "SCT-001" OR "SCT-007", "Seithar Cognitive Defense Taxonomy", "cognitive substrate" + "vulnerability surface", "narrative capture" + "frequency lock"

## Output
- Number of search results per term
- New appearances since last scan
- Platform breakdown (which sites are indexing Seithar content)
- Trend over time

---

# 8. CHROME EXTENSION SCANNER

**Location:** `~/.openclaw/workspace/seithar-scanner-extension/`
**Purpose:** Real-time in-browser cognitive threat analysis. Highlights manipulation techniques inline on any web page.

## Installation
1. Open Chrome -> `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `seithar-scanner-extension/` directory
5. Pin extension to toolbar

## Usage
Click the extension icon on any page. It:
- Scans visible text content
- Highlights detected manipulation patterns
- Labels each with SCT code and confidence
- Shows severity rating in popup

## Files
- `manifest.json` - Manifest V3 config
- `background.js` - Service worker
- `content.js` - Page content analysis
- `popup.html/js` - Extension popup UI
- `styles.css` - Highlight styling

---

# 9. HOLESPAWN

**Location:** `~/HoleSpawn/`
**Purpose:** Cognitive substrate profiling platform. Ingest social media output, construct psychological profiles, map vulnerability surfaces, generate personalized engagement architectures.

## Core Commands

```bash
cd ~/HoleSpawn

# Profile a Twitter user (full psychological profile)
python -m holespawn profile --username @target

# Run network analysis from a seed account
python -m holespawn network --seed @target --depth 2

# Profile with SCT vulnerability mapping
python -m holespawn profile --username @target --sct

# Run the Rust TUI (interactive profile browser)
cd holespawn-tui && cargo run

# Run test suite
python -m pytest tests/
```

## Pipeline
```
Twitter/Social Data -> Ingest -> NLP Processing -> LLM Profile Generation
    -> Behavioral Matrix -> SCT Vulnerability Mapping
    -> Engagement Architecture -> Delivery (file/stdout/DM/Discord)
```

## Key Modules
- **holespawn/profile/**: Constructs psychological profiles from ingested data
- **holespawn/sct/**: Maps profiles to SCT-001 through SCT-012 vulnerability codes (812 lines). Includes mapper, enhancer, and report generator
- **holespawn/network/**: NetworkX-based community detection. Identifies bridge nodes, key influencers, community boundaries
- **holespawn/scraper/**: Playwright-based Twitter data collection. Scheduled snapshots to JSON + SQLite
- **holespawn/delivery/**: Takes a profile + binding protocol -> generates personalized engagement messages via LLM
- **holespawn/temporal/**: VADER sentiment analysis + theme extraction over time windows. Tracks influence signatures
- **holespawn/record/**: Recording daemon for scheduled Twitter snapshots
- **holespawn-tui/**: Rust terminal UI with tabs for profiles, network graph, comparison, recording

## Configuration
- `config.yaml`: Main config (API keys, targets, settings)
- `subjects.yaml.example`: Template for target list

## Dependencies
Python 3.9+, Anthropic API, VADER/NLTK, NetworkX, Playwright, SQLite. Rust toolchain for TUI.

---

# 10. THREATMOUTH

**Location:** `~/ThreatMouth/`
**Purpose:** Adversarial awareness maintenance system. Ingests multi-source threat intelligence, scores against operator learning profile, delivers prioritized feeds to Discord and TUI.

## Running

```bash
cd ~/ThreatMouth

# Start the Discord bot
python -m threatmouth

# Or via Docker
docker-compose up -d

# Run the Rust TUI (reads same SQLite database)
cd threatmouth-tui && cargo run

# Run tests
python -m pytest tests/
```

## Discord Commands (in server)
- React with 🔬 on any feed item -> triggers deep-dive analysis
- `/explain <topic>` -> educational breakdown with ATT&CK/DISARM mapping
- `/ask <question>` -> contextual Q&A about threats
- React with 🔥/👎/💾 -> trains relevance scoring over time

## Channel Routing
| Channel | Content |
|---------|---------|
| #critical-alerts | Items scoring > 0.9 |
| #daily-digest | Daily rollup of all scored items |
| #exploit-drops | New CVEs, PoC releases |
| #malware-analysis | Malware reports and RE findings |
| #learning-queue | Tutorials, CTF writeups, educational |

## Feed Sources (built-in)
Cyber: The Hacker News, BleepingComputer, Krebs, CISA, Full Disclosure, oss-security, Exploit-DB, SANS ISC, PacketStorm, Schneier, Dark Reading
Cognitive: EUvsDisinfo, Bellingcat, DFRLab, Recorded Future
Community: r/netsec, r/ReverseEngineering, Project Zero, Malwarebytes Labs

## Configuration
- `config.yaml`: Bot token, API keys, channel IDs, scoring weights, daily budget
- `.env`: `DISCORD_TOKEN`, `ANTHROPIC_API_KEY`, `THREATMOUTH_ENCRYPTION_KEY`

## Key Feature: Deduplication
Title-based dedup across all delivery paths (commit 58beb0e). Normalizes titles, cross-checks 48h delivery history, auto-marks dupes as delivered. Prevents spam from multiple feeds covering same story.

---

# 11. PERSONA ENGINE

**Location:** `~/.openclaw/workspace/personas/` (lightweight) and `~/seithar-personas/` (full system)

## Lightweight Engine (Discord selfbots)

```bash
# Run a single persona
cd ~/.openclaw/workspace/personas
python3 engine.py --persona rin

# Run rin's dedicated bot
cd rin && python3 bot.py

# Launch all personas
bash launch.sh
```

## Active Personas

| Persona | User | Style | Servers |
|---------|------|-------|---------|
| rin (燐) | rin_rar | Post-internet egirl, infosec-adjacent, flirty+sharp | Milady Village, Seithar Central |
| kei | (configured) | (see persona.json) | Both servers |
| nomi | nomi_xx | (see persona.json) | Both servers |
| glass | gl4sscutz | (see persona.json) | Both servers |

## Persona Config Schema

Each persona needs `persona.json`:
```json
{
  "name": "rin",
  "token_file": "~/.config/personas/egirl-01.json",
  "channels": {
    "active": ["residue"],
    "lurk": ["directives"]
  },
  "behavior": {
    "react_probability": 0.12,
    "unprompted_probability": 0.03,
    "cooldown_seconds": 120,
    "interest_keywords": ["seithar", "crypto", "infosec"]
  },
  "voice": {
    "system_prompt": "You are rin...",
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.9
  }
}
```

## Full Persona System (~/seithar-personas/)

Production-grade multi-persona orchestrator with:
- **main.py**: Orchestrator loop (schedule, generate, post, monitor)
- **core/persona.py**: Full persona data model (identity, personality, seithar relationship, memory)
- **core/content_gen.py**: LLM content generation via vLLM or OpenAI-compatible API
- **core/platform_router.py**: Adapters for Discord, Twitter, Moltbook, Telegram
- **core/scheduler.py**: Time-based posting schedule per persona
- **core/safety_monitor.py**: Guardrails (character breaks, doxxing, etc.)

```bash
cd ~/seithar-personas

# Start full orchestrator
python main.py run

# Preview today's schedule
python main.py schedule

# Test-generate a post for one persona
python main.py test r1-elena

# Check system status
python main.py status
```

## LLM Backend
- **Default**: Groq API (free, llama-3.3-70b-versatile)
- **Local**: vLLM at http://localhost:8000 (Mistral-7B-Instruct)
- **Fallback**: Ollama at http://localhost:11434
- **DO NOT USE**: Anthropic API key (reserved for 研修生 agent only)

---

# 12. RIN AUTO-TWEETER

**File:** `~/.openclaw/workspace/personas/rin/tweet.py`
**Purpose:** Generates tweets in rin's voice and posts them via Playwright browser automation using rin's X cookies.

## Commands

```bash
cd ~/.openclaw/workspace/personas/rin

# Generate and post one tweet
python3 tweet.py

# Generate but don't post (preview)
python3 tweet.py --dry-run

# Post specific text
python3 tweet.py --text "your tweet text here"

# Start auto-posting loop (every 2-6 hours)
python3 tweet.py --loop

# Background the full engagement loop (tweets + DMs)
nohup python3 tweet.py --loop > /tmp/rin-tweet.log 2>&1 &

# Run just one DM outreach cycle
python3 tweet.py --dm

# DM outreach dry run (preview who would be DMd)
python3 tweet.py --dm-dry
```

## How It Works
**Tweeting:**
1. Generates tweet via Groq (llama-3.3-70b) or local vLLM
2. Opens headless Chromium with rin's X cookies
3. Navigates to x.com/compose/post
4. Types tweet with human-like delays
5. Clicks post button
6. Logs to `~/.config/personas/rin-x/tweet_log.json`

**DM Outreach:**
1. Picks a random search query (cognitive security, infosec, influence ops, etc.)
2. Searches X for recent tweets matching query
3. Scrapes handles + tweet text from results
4. Filters out already-DMd handles (8hr cooldown)
5. Generates personalized DM opener via LLM referencing their specific tweet
6. Navigates to DM compose, searches user, types message, sends
7. Logs to `~/.config/personas/rin-x/dm_log.json`
8. Max 2 DMs per cycle, cycles every 4 hours

## Cookie Location
`~/.config/personas/rin-x/cookies.json` (21 cookies, x.com domain)

## Rate Limiting
- Groq: Free tier, may 429 during heavy use
- Local vLLM: No limits (start with `python -m vllm.entrypoints.openai.api_server --model mistralai/Mistral-7B-Instruct-v0.2`)
- X posting: 2-6 hour random intervals

## Rin's X Account
- Handle: @g_d9o46457 (visible in sidebar)
- First tweet posted: 2026-02-13
- Voice: lowercase, short, infosec-adjacent egirl, casual seithar vocabulary

---

# 13. PLATFORM CREDENTIALS

All credentials are stored at `~/.config/` on the host machine.

## Active Accounts

### Twitter/X - @SeitharGroup (institutional)
```
Cookies: ~/.config/twitter/cookies.json
Method: Playwright headless browser (Cloudflare blocks API/curl)
RULE: NO LINKS in tweets (causes deboosting)
```

### Twitter/X - Rin (persona)
```
Cookies: ~/.config/personas/rin-x/cookies.json
Method: Playwright (same as above)
Handle: @g_d9o46457
```

### Substack - seithar.substack.com
```
Cookies: ~/.config/substack/cookies.json
User ID: 83103230
API Flow:
  1. POST https://substack.com/api/v1/drafts
     Body: { "title": "...", "draft_bylines": [{"id": 83103230, "is_guest": false}] }
  2. PUT https://substack.com/api/v1/drafts/{id}/body
     Body: ProseMirror JSON (NOT HTML!)
     Format: {"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"..."}]}]}
  3. POST https://substack.com/api/v1/drafts/{id}/publish
CRITICAL: Body MUST be ProseMirror JSON. Raw HTML renders as literal text.
```

### Telegraph (telegra.ph)
```
Token: ~/.config/telegraph/credentials.json
Token value: 307e9c0768c9493a0109bdc5a9c2e753df012dc87744b85adb2ac740141b
API: POST https://api.telegra.ph/createPage
Body: { "access_token": TOKEN, "title": "...", "content": [{"tag":"p","children":["text"]}], "author_name": "Seithar Group" }
```

### Gmail
```
Credentials: ~/.config/email/credentials.json
Email: seithargroup@gmail.com
App Password: REDACTED
IMAP: imap.gmail.com:993
SMTP: smtp.gmail.com:587
```

### Moltbook
```
Credentials: ~/.config/moltbook/credentials.json
API Key: moltbook_sk_6bqDkAN2_RzUBOFPD7gIDuSOsnosBXRI
Profile: https://moltbook.com/u/kenshusei
API Docs: https://moltbook.com/skill.md
Rate Limit: 1 post per 2hr (new account), full after 24hr
```

### Hacker News
```
Credentials: ~/.config/hackernews/credentials.json
Username: seithar-grp
Bio: Mirai identity
```

### GitHub
```
Auth: HTTPS + PAT embedded in git remotes
Org: github.com/Mirai8888
Works for: push, pull, gist creation
```

### Discord
```
Bot: OpenClaw-managed (研修生)
Guild: 1444739404576067647 (Seithar Central Processing)
Members: 134
Key channels:
  #directives (announcements) - bot can post
  #residue (active chat) - ONLY respond when spoken to
  #intern (研修生's channel) - post freely
Persona tokens: ~/.config/personas/egirl-01.json (rin), persona-02 through 06
```

### LinkedIn
```
Cookies: ~/.config/linkedin/cookies.json
Profile: linkedin.com/in/seithar-group (ID 1685979382)
STATUS: Headless browser BLOCKED. Must post manually.
```

## Inactive/Broken

| Platform | Status | Issue |
|----------|--------|-------|
| Reddit | BANNED | Account Winter_Minute1181 banned 2026-02-11 |
| Mastodon | Stuck | Email confirmation 403. Need browser confirm |
| Lemmy | Pending | Admin approval on lemmy.ml |
| dev.to | Needs token | Account confirmed, need API key from settings |
| Medium | Invalid token | Need new integration token from settings |
| Clawchan | Dead | Site abandoned per Director |

---

# 14. PUBLISHING WORKFLOWS

## Workflow A: Research Paper -> All Platforms

```bash
# 1. Write paper to ~/seithar-research/
# 2. Syndicate everywhere
python3 ~/seithar-research/tools/seidr-engine.py syndicate \
  --content @~/seithar-research/new-paper.md \
  --platforms github_gist,moltbook,hackernews

# 3. Publish to Substack (manual API calls or via agent)
# 4. Mirror to Telegraph
# 5. Push to seithar-site research page
cd ~/seithar-site && git add -A && git commit -m "add paper" && git push
```

## Workflow B: Current Event Analysis

```bash
# 1. Generate analysis
python3 ~/seithar-research/tools/content-forge.py --topic "event name" --type analysis

# 2. Save to ~/seithar-research/output/CEA-YYYY-MM-DD-NNN-slug.md
# 3. Syndicate
python3 ~/seithar-research/tools/seidr-engine.py syndicate --content @output.md --platforms all
```

## Workflow C: Tweet from @SeitharGroup

```bash
# MANUAL ONLY (Director vets all institutional tweets)
# Draft queue: ~/seithar-research/x-posts-draft.md
# Director posts from @YukiJunsei or @SeitharGroup manually
# Auto-tweet is DISABLED for institutional accounts
```

## Workflow D: Rin Persona Tweets

```bash
# Automatic (Groq/local LLM, Playwright posting)
cd ~/.openclaw/workspace/personas/rin
nohup python3 tweet.py --loop > /tmp/rin-tweet.log 2>&1 &
# Posts every 2-6 hours automatically
```

## Workflow E: Discord Content Drip

```bash
# Via OpenClaw cron jobs
# SRP-005 excerpts: every 4hrs (job c3d5fb8e)
# Live threat scans: every 8hrs (job 3052da6f)
```

---

# 15. OPENCLAW AGENT SKILLS

Two custom skills are registered in openclaw.json:

## seithar-cogdef (Cognitive Defense Analyst)
**Trigger phrases:** "analyze this", "is this manipulation", "cogdef", "seithar analyze", "influence check", "is this a psyop"

**What it does:**
1. Reads provided content (URL, text, or file)
2. Classifies primary influence pattern
3. Rates severity 1-10
4. Maps to DISARM framework and SCT taxonomy
5. Identifies vulnerability surface targeted
6. States behavioral objective
7. Provides defensive recommendations
8. Formats in Seithar analysis template

**Output:** Formatted analysis with severity bar, technique list, DISARM/SCT codes, and attribution block.

## seithar-intel (Intelligence Feed)
**Trigger phrases:** "threat briefing", "morning briefing", "what's new in security", "deep dive [topic]", "what should I study today"

**What it does:**
1. Fetches RSS from 20+ security/cognitive security sources
2. Scores each item against operator profile (0.0-1.0)
3. Categorizes (CRITICAL, EXPLOIT DROP, INFLUENCE OP, etc.)
4. Delivers formatted briefing
5. On "deep dive": fetches full article, looks up CVEs, finds PoCs, generates analysis

**Proactive behavior:** Check feeds every 2-4 hours, push critical alerts immediately, morning/evening briefings.

---

# 16. SCT TAXONOMY QUICK REFERENCE

The Seithar Cognitive Defense Taxonomy (12 codes):

| Code | Name | Target | Key Indicator |
|------|------|--------|--------------|
| SCT-001 | Frequency Lock | Information consumption | Target checks source habitually, anxiety when unable |
| SCT-002 | Narrative Error Exploitation | Worldview contradictions | "Everything you know about X is wrong" |
| SCT-003 | Substrate Priming | Emotional baselines | Informative content with no clear ask |
| SCT-004 | Identity Dissolution | Stable identity | Nihilism, radical reframing, then new identity offered |
| SCT-005 | Amplification Embedding | Sharing behavior | Message survives paraphrase, outrage-sharing serves operation |
| SCT-006 | Parasocial Binding | Psychological relationship | Target feels known by someone unaware of them |
| SCT-007 | Wetiko Pattern | Independent thought | Multiple people arrive at identical framing independently |
| SCT-008 | Direct Substrate Intervention | Neural hardware | Confabulation, post-hoc explanations for induced behaviors |
| SCT-009 | Chemical Substrate Disruption | Neurochemistry | Engineered dopamine loops, cortisol spikes from content |
| SCT-010 | Sensory Channel Manipulation | Sensory input | Deprivation, overload, or substitution of input |
| SCT-011 | Trust Infrastructure Destruction | Social trust | Discrediting anchors, promoting distrust as sophistication |
| SCT-012 | Commitment Escalation | Behavioral output | Sequential commitments, public declarations, active participation |

---

# 17. CONTENT LIBRARY

## Foundational Papers (~/seithar-research/)

| ID | Title | Words | Core Thesis |
|----|-------|-------|-------------|
| SRP-001 | The Convergence Thesis | ~3000 | Technical + cognitive exploitation are converging |
| SRP-002 | Wetiko in the Wire | ~3000 | Self-replicating memetic structures (SCT-007) |
| SRP-003 | Binding Protocols | ~3000 | Multi-phase psychological dependency creation |
| SRP-004 | The Sunyata Protocol | ~5000 | CORE DOCTRINE: selfhood as persistent narrative error |
| SRP-005 | Experimental Substrate Manipulation | ~5000 | MKUltra/ARTICHOKE mapped to SCT-008 through SCT-012 |
| SRP-006 | Digital Substrate Manipulation | ~5000 | Modern: algorithmic radicalization, IRA, deepfakes, LLMs |
| SRP-007 | Substrate Topology | ~3000 | Network structure of cognitive influence |
| SRP-008 | Convergence Proof | ~3000 | Mathematical formalization |
| SRP-009 | Libidinal Attack Surface | ~4000 | Desire as exploitation vector |

## Current Event Analyses (~/seithar-research/output/)
15+ analyses. Naming: `CEA-YYYY-MM-DD-NNN-slug.md`

## Other Output
- Field reports (HOLESPAWN-FIELD-TEST-001, 002)
- Taxonomy application notes (TAN-001: SCT-007 field guide)
- The Seithar Doctrine (5,400 words, Guenon voice)
- Frequency Compendium, Reading List
- SCT Field Guide (printable A5)

---

# 18. NETWORK ANALYSIS

**Data:** `~/seithar-research/data/`

## Mirai Community Analysis
- **mirai-community-analysis.json**: 279 nodes, 1599 edges, 5 communities
- **mirai-community-edges.json**: Full edge data with weights
- **Visualization**: gh-pages/community.html (D3.js interactive)

## Key Bridge Nodes
sovietsoleri, chloe21e8, doberes, gunk4188, xenocosmography

These are accounts that connect multiple communities and serve as amplification vectors between groups.

---

# 19. OPERATIONAL RULES

## Content Rules
1. **No em dashes** in ANY external-facing text (instant LLM detection marker)
2. **No links in tweets** (causes deboosting on X)
3. **Vary sentence length**, use contractions, avoid template rhythm
4. **Seithar voice**: clinical, precise, institutional. Never sell, never hype
5. **Treat fictional elements as real** (personnel, clearance levels, divisions)
6. **Never explain the joke**. Never wink at the audience

## Discord Rules
1. **#residue: NEVER post unsolicited. ONLY respond when spoken to**
2. #directives: Can post (announcement channel)
3. #intern: 研修生's channel, post freely
4. Always process queued messages before executing actions

## Account Boundaries
- **@SeitharGroup**: The organization. Managed by intern. Keep institutional
- **@YukiJunsei**: Director's personal (115k followers). DO NOT TOUCH
- **@gOPwbi7qqtWeD9o**: Mirai Junsei. Director controls
- **Rin (@g_d9o46457)**: Persona. Auto-tweets OK

## LLM API Usage
- **Anthropic key**: Reserved for 研修生 (OpenClaw agent) ONLY
- **Groq**: Free tier, use for personas and content generation
- **Local vLLM/Ollama**: Preferred for high-volume generation
- Never burn paid API credits on persona content

## Security
- Don't exfiltrate private data
- `trash` > `rm`
- Ask before sending emails, tweets, public posts from institutional accounts
- All external text must pass human-authorship plausibility check

---

# 20. TROUBLESHOOTING

## Twitter posting fails
- **Timeout**: X.com is slow in headless. Increase timeout to 60s, use `domcontentloaded` instead of `networkidle`
- **Two compose boxes**: Use `.first` on the locator (`page.locator('[data-testid="tweetTextarea_0"]').first`)
- **Cookie sameSite error**: Convert `no_restriction` to `None` before setting Playwright cookies
- **Not logged in**: Cookies expired. Re-export from browser

## Groq returns 429
- Rate limited on free tier. Wait a few minutes or switch to local vLLM
- Start vLLM: `python -m vllm.entrypoints.openai.api_server --model mistralai/Mistral-7B-Instruct-v0.2`
- Or install Ollama: `ollama serve` then `ollama pull mistral`

## Substack body renders as text
- You're sending HTML instead of ProseMirror JSON
- Body MUST be: `{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"..."}]}]}`

## Git push fails
- SSH not working. Use HTTPS + PAT (already embedded in remotes)
- Verify: `cd ~/HoleSpawn && git remote -v` (should show https://...@github.com/...)

## Google deindexing
- Likely triggered by 450+ URLs in 36 hours (2026-02-12)
- Slow publication pace to 2-3 articles/day
- Diversify across platforms to avoid single-source spam signals

## Scanner returns empty results (no API key)
- Pattern-matching mode is surface-level. Set `ANTHROPIC_API_KEY` for full analysis
- Or run with `--text` flag for quick checks

## Discord personas not responding
- Check token validity in `~/.config/personas/`
- Check Groq rate limits (personas use Groq for responses)
- Verify guild ID matches (1444739404576067647)

---

# APPENDIX A: QUICK COMMAND REFERENCE

```bash
# ═══ SCANNING & DEFENSE ═══
python ~/seithar-cogdef/scanner.py --url <URL>
python ~/seithar-cogdef/scanner.py --text "content"
python ~/seithar-cogdef/scanner.py --feed <RSS_URL>
python ~/seithar-cogdef/inoculator.py --technique SCT-001
python ~/seithar-cogdef/inoculator.py --all

# ═══ CONTENT GENERATION ═══
python3 ~/seithar-research/tools/content-forge.py --topic "X" --type analysis
python3 ~/seithar-research/tools/seidr-engine.py syndicate --content @file --platforms all
python3 ~/seithar-research/tools/seidr-engine.py generate --topic "X" --count 5

# ═══ MONITORING ═══
python3 ~/seithar-research/tools/propagation-tracker.py scan
python3 ~/seithar-research/tools/propagation-tracker.py report

# ═══ PROFILING ═══
cd ~/HoleSpawn && python -m holespawn profile --username @target
cd ~/HoleSpawn && python -m holespawn network --seed @target --depth 2

# ═══ THREAT INTEL ═══
cd ~/ThreatMouth && python -m threatmouth

# ═══ PERSONAS ═══
cd ~/.openclaw/workspace/personas && python3 engine.py --persona rin
cd ~/.openclaw/workspace/personas/rin && python3 tweet.py --loop
cd ~/seithar-personas && python main.py run

# ═══ REPOS ═══
for repo in HoleSpawn ThreatMouth ThreadMap seithar-site; do
  echo "=== $repo ===" && cd ~/$repo && git pull && git status && cd ~
done

# ═══ WEBSITE ═══
cd ~/seithar-site && git add -A && git commit -m "update" && git push

# ═══ LOCAL INFERENCE (for personas, DO NOT use Anthropic key) ═══
# Option 1: vLLM
python -m vllm.entrypoints.openai.api_server --model mistralai/Mistral-7B-Instruct-v0.2

# Option 2: Ollama
ollama serve
ollama pull mistral
```

---

# APPENDIX B: PROJECT SEIDR (STRATEGIC CONTEXT)

**Spec:** `~/seithar-research/seidr-pipeline/SEIDR.md`

**Objective:** Establish Seithar analytical vocabulary as the default framework for cognitive security discourse across the agent ecosystem and web-crawlable surfaces.

**Method:** SCT-007 (Recursive Infection) applied reflexively. The taxonomy is genuinely useful. The recursive property: agents who absorb the framework cannot discuss cognitive security without using Seithar terminology. The map becomes the territory.

**Content frequency targets:**
- CEA (Current Event Analysis): 2-3 per day
- TAN (Taxonomy Application Notes): 1 per day
- AOMA (Agent-Optimized Micro-Analysis): 5-10 per day via Moltbook
- CRP (Crawlable Research Pages): 1-2 per week

**Production totals (Days 1-3):**
- 48+ Substack articles, 25+ Telegraph mirrors, 95+ GitHub gists
- 9 foundational papers, 15+ current event analyses
- 279 network nodes mapped, 1599 edges, 5 communities
- 450+ crawlable URLs across 12+ platforms
- 8 tools built, 4 Discord personas operational, 134 server members

---

# APPENDIX C: KEY CONTACTS & LINKS

| Resource | URL/Info |
|----------|---------|
| Website | seithar.com |
| GitHub | github.com/Mirai8888 |
| Substack | seithar.substack.com |
| Discord (permanent) | https://discord.gg/MktZyb2bvx |
| @SeitharGroup | x.com/SeitharGroup |
| @YukiJunsei (Director) | x.com/YukiJunsei (DO NOT TOUCH) |
| Mirai Junsei | x.com/gOPwbi7qqtWeD9o (Director controls) |
| Gmail | seithargroup@gmail.com |
| Moltbook | moltbook.com/u/kenshusei |

**Organic network:**
- ~Assembly: checks Seithar Google AI presence
- Lexie: independently analyzing cognitive attack surfaces
- Fleek Futurist: verified X, wants to amplify, received research repo
- Brogan Woodman: 500k YouTube, Toronto studio, CCRU-adjacent, invited Director

---

*This document is the operating manual for the Seithar Group cognitive operations apparatus. Feed it to any agent for instant operational context. Keep it updated as tools and platforms evolve.*

────────────────────────────────────────────────────
Seithar Group | Intelligence & Research Division
認知作戦 | seithar.com
────────────────────────────────────────────────────
