# SCT Scanner v2 — Subliminal Detection Layer

## Problem (Director Feedback, 2026-02-13)

v1 detects surface-level manipulation — fear appeals, authority claims, tribal markers.
"Great for identifying things a lot of people can register as bullshit."
"Most of the attack vectors are very easy to identify."
"A huge amount of people understand 'Trust no one' and 'Keep watching' as QAnon-era shibboleths."
"Linguistically what's required is a more subliminal understanding."

## What v1 Catches (Surface Layer)
- Keyword matching: "urgent", "share this", "wake up", "they don't want you to know"
- Explicit emotional manipulation markers
- Direct authority appeals
- Obvious tribal signaling

## What v2 Must Catch (Structural Layer)

### 1. PRESUPPOSITION LOADING
The attack is in what's ASSUMED, not what's STATED.

**Pattern**: Embedding contested claims as grammatical presuppositions.
- "When did the economy start failing?" (presupposes failure)
- "Another example of media bias..." (presupposes established pattern)
- "The real question is..." (presupposes all prior questions are wrong)

**Detection**: Parse sentence structure for presuppositional triggers:
- Definite descriptions ("the crisis", "the corruption")
- Temporal clauses ("since X began", "after X happened")
- Factive verbs ("realize", "notice", "discover", "reveal")
- Change-of-state verbs ("stop", "start", "continue")
- Cleft constructions ("It was X who...")
- Comparative/superlative presuppositions

### 2. FRAME CONTROL
The container determines what can be thought inside it.

**Pattern**: Setting the interpretive frame so all possible responses serve the operator.
- False dichotomies: "either you support X or you support Y" (eliminates third options)
- Loaded questions: "Why is [contested claim] happening?"
- Overton window manipulation: presenting extreme position to make moderate version seem reasonable
- Category manipulation: reclassifying an action ("protest" → "riot", "torture" → "enhanced interrogation")

**Detection**: 
- Binary framing markers ("either/or", "you're either with us or")
- Forced-choice constructions
- Euphemism chains (match against known euphemism databases)
- Reframing markers ("actually", "what's really happening", "let's call it what it is")

### 3. NARRATIVE LAUNDERING
Clean the source by routing through trusted intermediaries.

**Pattern**: Adversarial content enters mainstream discourse through:
- Academic citation of planted studies
- Journalist covering "controversy" (laundering via reporting)
- "Just asking questions" (JAQ-ing off)
- Aggregation sites stripping original sourcing

**Detection**:
- Source attribution analysis (does the claim trace to primary evidence?)
- "Some say" / "people are saying" / "reports suggest" (vague attribution)
- Circular citation patterns (A cites B cites A)
- Controversy laundering markers ("the debate over", "growing questions about")

### 4. EMOTIONAL PRIMING SEQUENCES
Not individual emotions — sequences designed to lower cognitive defenses.

**Pattern**: Content structured to walk through emotional states:
- Outrage → Identification → Solution → Action
- Fear → Scarcity → Urgency → Commitment  
- Belonging → Threat-to-belonging → Defense → Radicalization

**Detection**:
- Sentiment trajectory analysis across paragraphs
- Emotional intensity escalation patterns
- Solution positioning after emotional peak
- Call-to-action placement relative to emotional arc

### 5. STATISTICAL MANIPULATION
Using real numbers to create false impressions.

**Pattern**:
- Base rate neglect (big number without context)
- Relative vs absolute risk framing
- Cherry-picked timeframes
- Survivorship bias in examples
- Simpson's paradox exploitation

**Detection**:
- Numerical claims without denominators
- Percentage claims without base rates
- "X times more likely" without absolute risk
- Selective date range indicators

### 6. IDENTITY INTERPELLATION
Hailing the subject into a position before they choose it.

**Pattern**: "As a [parent/patriot/taxpayer/professional], you..."
- Activates identity before presenting claim
- Claim is then processed through identity lens, not rational evaluation
- More subtle version: "If you care about X..." (constructs identity through care-claim)

**Detection**:
- "As a [identity]" constructions
- "If you're someone who..." conditional identity framing
- "People who [identity marker] know that..."
- "Real [identity] would never..."

### 7. TEMPORAL MANIPULATION
Controlling the perceived timeline to control interpretation.

**Pattern**:
- Anchoring to a mythical past ("things used to be...")
- Inevitability framing ("it's only a matter of time")
- Manufactured nostalgia as political tool
- False urgency disconnected from actual timelines

**Detection**:
- Past-tense idealization markers
- Inevitability language without causal mechanism
- Urgency claims without verifiable deadlines
- "Remember when" as argumentative premise

## Implementation Notes

### Approach: Hybrid (Pattern + LLM)
- **Pattern matching** for structural markers (presupposition triggers, frame indicators)
- **LLM analysis** for context-dependent detection (is this presupposition contested? is this frame manipulative or simply organizational?)
- **Scoring**: Structural detections weighted higher than keyword matches
- **Output**: Each detection includes the STRUCTURAL MECHANISM, not just the surface pattern

### New SCT Subcodes
Consider extending taxonomy:
- SCT-001a: Narrative Capture — Presuppositional
- SCT-001b: Narrative Capture — Frame Control
- SCT-003a: Substrate Priming — Emotional Sequence
- SCT-006a: Consensus Manufacturing — Narrative Laundering
- SCT-008a: Temporal Distortion — Manufactured Nostalgia

### Priority
High — this is what differentiates Seithar from every other "disinformation detector."
Everyone catches the obvious stuff. Nobody catches the structural layer.
That gap IS our value proposition.
