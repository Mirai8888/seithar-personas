# INFERENCE PLAN — Cost Optimization Without Quality Loss

## Current Spend Profile
- ~$400 over 3 days (Feb 11-13)
- Primary cost: Opus for everything (main session, crons, sub-agents, writing)
- Opus: ~$15/M input, ~$75/M output tokens

## Model Tiers

| Tier | Model | Cost (output) | Use For |
|------|-------|--------------|---------|
| **S-tier** | Claude Opus 4 | $75/M | Research papers, strategic writing, complex analysis, Director conversations |
| **A-tier** | Claude Sonnet 4 | $15/M | Cron jobs, routine scanning, platform engagement, code generation, C2 dashboard |
| **B-tier** | Claude Haiku 3.5 | $4/M | Simple queue checks, status monitoring, data formatting |
| **Free** | Groq (Llama 3.3 70B) | $0 | FLESHENGINE LLM assessments (already using) |
| **Free** | Local keyword scoring | $0 | FE scanner (878 keywords, no LLM needed) |

## Optimization Actions

### Already Done
- [x] FLESHENGINE scanner cron → Sonnet ($15 vs $75/M)
- [x] Moltbook presence cron → Sonnet
- [x] FLESHENGINE LLM assessments → Groq free tier (Llama 3.3 70B)
- [x] FE keyword scoring → zero cost (local Python)
- [x] Structural pattern detection → zero cost (local Python)

### Immediate Savings
- [ ] Heartbeat checks → Haiku ($4/M) — these are just "check HEARTBEAT.md, reply OK"
- [ ] Empty queue checks → reduce frequency (5min→10min when queue empty)
- [ ] Sub-agent writing tasks → Sonnet first draft, Opus for revision only

### Medium-term (1-2 weeks)
- [ ] Local 7B model for persona operation — eliminates API cost for 20 agents
- [ ] Batch content generation — produce multiple pieces per session instead of one-at-a-time
- [ ] Template-based content (Content Forge) — reduces per-piece inference to near zero

### Long-term (Seithar Stack)
- [ ] Self-hosted inference (RTX 4090 or cloud GPU) — ~$1/hr vs $75/M output
- [ ] Fine-tuned model on Seithar voice — better output, fewer tokens needed
- [ ] All crons on local model — zero ongoing API cost for maintenance ops

## Cost Estimates (Post-Optimization)

### Current: ~$130/day on Opus for everything
### After immediate changes: ~$40-60/day
  - Main session (Opus): ~$30/day (Director interactions + strategic work)
  - Crons (Sonnet): ~$5/day (2 crons, routine operations)
  - Sub-agents (Sonnet): ~$5-15/day (writing tasks)
  - Groq + local: $0/day (FLESHENGINE scoring)

### After local model: ~$20-30/day
  - Main session only on Opus
  - Everything else local or Sonnet
  - Personas on local 7B (free)

## Rules
1. **Director conversation = always Opus** (no quality compromise on strategic interaction)
2. **Research papers / Substack articles = Opus** (voice quality matters)
3. **Cron jobs = Sonnet or cheaper** (routine execution, doesn't need genius)
4. **Queue checks with no work = minimize** (pure waste)
5. **Use tools over inference** (keyword banks > LLM scoring, templates > freeform generation)
6. **Batch operations** (one session produces 5 articles > 5 sessions producing 1 each)

## Key Principle
Every tool we build reduces future inference cost. The scanner runs on keywords (free). The Content Forge runs on templates (free). The more we invest in tooling now, the less we spend on inference later. **Tooling is the hedge against API costs.**
