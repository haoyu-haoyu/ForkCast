# UI Overhaul — Design Plan (Phase 1)

## 1. Grounding: what world does this thing live in?

ForkCast is a governance/audit instrument. Its native objects are **checkpoints,
receipts, manifests, cryptographic commitments, regulatory documents, control
rooms**. The people it serves sign things, stamp things, file things, and get
audited on them. The aesthetic follows from that world:

- **The registry, not the dashboard.** Paper-and-ink document surfaces, ruled
  tables, filed evidence — not gradient SaaS cards.
- **The instrument, not the toy.** Dense, legible, tabular numerals, everything
  labeled, nothing decorative that isn't also informative.
- **The receipt as proof.** The product's whole thesis is "you can verify what
  was approved." The UI should make the proof artifact — the audit manifest and
  its Kaspa anchor — physically recognizable.

## 2. Token system

### Color — 6 named inks on paper (semantic status is first-class)

| Token | Hex | Role |
|---|---|---|
| `ink` | `#182420` | Text, wordmark, filled controls (deep green-black, not pure black) |
| `paper` | `#F2F4F0` | Page ground (cool gray-green; surfaces are #FFFFFF white cards on it) |
| `verify` | `#157A55` | APPROVED · HIT · BALANCED HIT · anchored · safe (registry green) |
| `signal` | `#96660B` | PENDING · PARTIAL · warnings · human-review-required (ledger amber; retained from the pre-overhaul palette after the first-draft #A96F0E failed WCAG AA in review) |
| `alarm` | `#B3261E` | MISS · REJECTED · danger · errors (stamp red) |
| `registry` | `#2D5B9E` | Links, references, evidence pointers, neutral info (archive blue) |

Derived (not named colors, computed tints): each status color gets a `-tint`
background (~92% toward white) and a `-line` border (~55% toward white); muted
text and hairlines derive from `ink` (`#5C6A64` muted, `#DCE2DC` rule).

### Type — three faces, self-hosted woff2 only (no CDN)

- **Display: Space Grotesk 500/700** — headings, step titles, big metric
  numerals, the wordmark. Characterful, slightly technical; used with restraint
  (never below 15px).
- **Body: IBM Plex Sans 400/500/600** — the workhorse. Plex was drawn for
  enterprise instrumentation; it reads "engineering document" without being cold.
- **Mono: IBM Plex Mono 400/600** — hashes, txids, run ids, evidence pointers,
  diff lines, the receipt. Sibling of the body face, so data and prose sit
  together naturally.

Scale: 11 (overline) / 12.5 / 13.5 (body) / 15 / 18 / 22 / 28 / 44 (display),
1.5 line height for prose, tabular numerals everywhere data lives.

### Spacing / radius / elevation

- Spacing scale: 4 / 8 / 12 / 16 / 24 / 32 / 48.
- Radius: interactive controls 8px; cards 12px; pills 999px; **the receipt is
  square-edged with perforated ends** (the one deliberate exception — paper
  tape has no border-radius).
- Elevation: exactly two levels. Cards: `0 1px 2px rgba(24,36,32,.05), 0 8px
  24px rgba(24,36,32,.05)`. The receipt: a slightly stronger paper shadow to
  lift it off the panel. Nothing else floats.

## 3. Signature element: THE RECEIPT

One bold move, everything else disciplined: **the audit manifest is rendered as
a literal paper-tape receipt**, persistent in the right rail on every screen,
and scaled up on the Audit + Kaspa screen.

- Perforated top and bottom edges (CSS radial-gradient mask — no images).
- Mono type, dotted leader lines between label and value, ruled item rows for
  the 8 artifact hashes.
- The Kaspa anchor is the **stamp**: a rotated, double-ruled seal reading
  ANCHORED · TN-10 in `verify` green (it would print in `signal` amber for
  local-only packages). The f553… txid prints under it as the receipt's serial.
- The same tape treatment carries the hash-chain (h0→h4) block on the live-run
  path, so "chained run" and "legacy run" receipts read as the same artifact
  family.

Everything else — cards, tables, feeds — stays quiet: white surfaces, hairline
rules, semantic pills, generous whitespace.

## 4. Known weaknesses this plan fixes (Pass B targets)

1. **Run controls is near-empty** → becomes a two-column "run parameters"
   sheet: controls left; right column restates (rearranged, not invented) the
   run envelope — mode Replay, events cached 128, window 90 days, seed state —
   plus the run-action buttons, so the screen reads as a real pre-flight check.
2. **Uniform card weight** → three tiers: hero panels (checkpoint cards, chain
   box), standard cards, and quiet list rows. Tier shows in border, shadow and
   heading size, not in color noise.
3. **Weak hierarchy** → Space Grotesk display steps + overline labels; each
   screen gets exactly one dominant element.
4. **Undifferentiated status pills** → one pill grammar: APPROVED/HIT solid
   `verify` tint with dot; PENDING/PARTIAL `signal` tint; MISS/REJECTED `alarm`
   tint; provenance badges quieter (outline only) so verdicts outrank metadata.

## 5. Self-critique against AI-default looks

- ~~Cream + high-contrast serif + terracotta~~ — no cream (cool gray-green
  paper), no serif anywhere, no terracotta. The display face is a grotesk.
- ~~Near-black + single acid accent~~ — light theme; four semantic colors do
  real work; `ink` is a green-black used for text, not a void background.
- ~~Broadsheet hairlines + zero radius everywhere~~ — cards and controls are
  visibly rounded; hairlines exist but sit on soft-shadowed white surfaces.
  Square edges appear ONLY on the receipt, as a conscious, justified quote of
  paper tape.
- One theme (confident light). No toggle, no dark mode, no new modes.

## 6. Build order (Phase 2)

- **Pass A** — self-host fonts (OFL woff2 in `web/public/fonts/`), swap token
  system, type scale. Commit.
- **Pass B** — hierarchy tiers, pill grammar, Run-controls two-column build-out,
  card weight differentiation. Commit.
- **Pass C** — the receipt (sidebar + Audit+Kaspa + live hash chain), key-screen
  polish (Checkpoint Control Panel, Approve extraction, Blind rubric, Impact
  report). Commit.
- **Pass D** — micro-interactions: focus rings, hovers, ONE orchestrated
  transition (main-stage step change: 240ms fade/rise), all wrapped in
  `@media (prefers-reduced-motion: no-preference)`. Commit.

Hard invariants (runs/** bytes, data copies, protected strings, English-only,
es2020, no new runtime deps, no storage APIs, all 10 steps + 4 checkpoints +
persona chat + hard limits + live path functional) are restated in
OVERHAUL_INVENTORY.md and verified in Phase 3.
