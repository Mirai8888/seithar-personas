# Seithar.com Style Guide — Design Reference

Extracted from seithar.com for use in all future visualizations and web assets.

## Color Palette

| Element | Color | Hex |
|---------|-------|-----|
| Background | White | `#FFFFFF` |
| Primary text | Near-black | `#1A1A1A` |
| Secondary text | Dark gray | `#666666` |
| Tertiary text | Light gray | `#999999` |
| Borders | Light gray | `#E0E0E0` |
| Card background | Off-white | `#FAFAFA` |
| Card photo bg | Lighter gray | `#F0F0F0` |
| Modal overlay | Black 80% | `rgba(0,0,0,0.8)` |
| Modal bg | Pure black | `#000000` |
| Modal text | White | `#FFFFFF` |
| Modal border | White | `#FFFFFF` |

**Rule:** White background, near-black text, grayscale only. NO colors. The site is monochromatic.

## Typography

| Element | Font | Weight | Size | Tracking | Case |
|---------|------|--------|------|----------|------|
| Body | System sans (-apple-system, Helvetica Neue) | 400 | — | Normal | — |
| Main timer/heading | Same | 300 (light) | 6vw | 0.15em | Sentence |
| Navigation links | Same | 400 | 0.9vw | 0.08em | UPPERCASE |
| Status/footer | Same | 300 | 0.7vw | 0.12em | UPPERCASE |
| About heading | Same | 400 | 1.8vw | 0.1em | UPPERCASE |
| About body | Same | 300 | 1vw | 0.02em | Normal |
| Page title | Same | 300 | 1.2vw | 0.05em | Normal |
| Card name | Same | 400 | 1.2rem | 0.08em | UPPERCASE |
| Card title | Same | — | 10px | 3px | UPPERCASE |
| Meta labels | Same | — | 9px | 1px | UPPERCASE |
| Spec tags | Same | — | 9px | 1.5px | UPPERCASE |
| Bio text | Same | 300 | 12px | — | Normal |
| Modal | Monospace | — | 0.85-0.9rem | 0.1em | UPPERCASE (header) |

**Key rules:**
- System sans-serif stack (no custom fonts)
- Light weight (300) dominates
- Wide letter-spacing on everything
- UPPERCASE for labels, navigation, headers
- Line-height generous (1.6-2.0)
- `-webkit-font-smoothing: antialiased`

## Layout

- Centered container, `padding: 8vh 8vw`
- About pages: left-aligned, `padding: 12vh 12vw`, `max-width: 60vw`
- Generous whitespace everywhere
- Flexbox column layouts, `gap: 4vh`
- Cards: 1px border `#E0E0E0`, hover to `#1A1A1A`

## Navigation Style

Links wrapped in `[ BRACKETS ]` — terminal/archival aesthetic:
```
[ SIGN WAIVER ]
[ ABOUT US ]
[ CHAT WITH US ]
```

## Interactions

- Hover: `opacity: 0.5` with `0.2s ease` transition
- Card hover: border-color darkens
- No color changes on hover — opacity only
- Background: optional grayscale video at 30% opacity

## Modal Style (for popups/overlays)

- Black background, white 1px border
- Monospace font
- White text on black
- Pre-wrap text
- Max-width 600px

## Key Principles

1. **Monochromatic** — white/black/gray only, no accent colors
2. **Minimalist** — vast whitespace, sparse content
3. **Institutional** — uppercase labels, wide tracking, thin weights
4. **Clinical** — no decoration, no gradients, no rounded corners
5. **Terminal aesthetic** — bracket navigation, monospace for modals
6. **Responsive** — vw-based sizing, mobile breakpoint at 768px

## For Visualizations (D3.js, etc.)

When building network graphs or data visualizations for Seithar:
- Use white/light background instead of dark terminal theme
- Node colors: grayscale shades (#1A1A1A, #666, #999, #CCC)
- If color needed for categories: muted, desaturated tones only
- Text: system sans, light weight, wide tracking, uppercase labels
- Tooltips: black bg, white text, 1px white border, monospace
- Controls: bracket-style `[ FILTER ]` `[ RESET ]`
- No glows, no neon, no terminal green
- Hover: opacity transitions, not color changes
