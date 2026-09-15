---
name: TFT Tracker
description: An editorial match-review desk for serious TFT players.
colors:
  ink-deep: "#060a10"
  ink-surface: "#0a1019"
  ink-raised: "#101925"
  ink-active: "#182333"
  mineral-paper: "#f0ede5"
  mineral-paper-muted: "#dedbd3"
  text-primary: "#f3f0e9"
  text-muted: "#9ba8b8"
  text-secondary: "#c2cad4"
  violet-selection: "#8873ee"
  violet-deep: "#5e4bbd"
  cobalt-data: "#5d82ef"
  amber-state: "#e6b85c"
  red-state: "#dc6372"
  rule-soft: "rgba(197, 211, 228, 0.15)"
  rule-strong: "rgba(197, 211, 228, 0.28)"
  placement-first: "#80a9ff"
  placement-second: "#6f96f1"
  placement-third: "#5d82dd"
  placement-fourth: "#496ab8"
  placement-fifth: "#d77980"
  placement-sixth: "#c6626c"
  placement-seventh: "#aa4c5b"
  placement-eighth: "#833846"
typography:
  display:
    fontFamily: "Outfit, Segoe UI, sans-serif"
    fontSize: "42px"
    fontWeight: 650
    lineHeight: 1.02
    letterSpacing: "-0.035em"
  metric:
    fontFamily: "Outfit, Segoe UI, sans-serif"
    fontSize: "clamp(52px, 5vw, 76px)"
    fontWeight: 650
    lineHeight: 1
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Outfit, Segoe UI, sans-serif"
    fontSize: "20px"
    fontWeight: 650
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Outfit, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Outfit, Segoe UI, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    letterSpacing: "0"
rounded:
  data: "2px"
  control: "4px"
  repeated-card: "6px"
  dialog: "8px"
  compact-pill: "13px"
spacing:
  xxs: "5px"
  xs: "10px"
  sm: "14px"
  md: "20px"
  lg: "30px"
  xl: "44px"
  dialog: "56px"
components:
  button-primary:
    backgroundColor: "{colors.violet-selection}"
    textColor: "{colors.ink-deep}"
    rounded: "{rounded.control}"
    padding: "0 17px"
    height: "40px"
  input-field:
    backgroundColor: "{colors.ink-raised}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.control}"
    padding: "0 12px"
    height: "40px"
  analysis-panel:
    backgroundColor: "{colors.ink-surface}"
    textColor: "{colors.text-primary}"
    rounded: "0"
    padding: "30px"
  match-ledger:
    backgroundColor: "{colors.mineral-paper}"
    textColor: "{colors.ink-deep}"
    rounded: "0"
    padding: "30px"
---

# Design System: TFT Tracker

## Overview

**Creative North Star: "The Matchroom Ledger"**

TFT Tracker is a post-game review desk: part tournament broadcast, part analyst notebook, and part polished desktop application. It is built for repeated personal analysis, so expression comes from composition, typography, and game-specific data language rather than decorative chrome.

The system alternates dense ruled analysis fields with one decisive mineral-paper ledger surface. Key performance numbers stand in open space. Repeated cards are reserved for repeated objects such as comps; the page itself is organized as connected editorial bands.

**Key Characteristics:**

- An asymmetric player masthead with the tactician integrated into identity.
- A mineral-paper twenty-game ledger as the signature first-viewport surface.
- Open, tabular performance numerals without nested metric cards.
- Flat ink surfaces divided by precise rules instead of glow or broad shadow.
- Blue placements for first through fourth and red placements for fifth through eighth.
- Fast, interruptible interaction feedback with a reduced-motion equivalent.

## Colors

The palette combines blue-black ink, warm mineral paper, and a restrained violet identity accent. Cobalt and red are functional data colors rather than decoration.

### Primary

- **Violet Selection** marks active navigation, primary actions, focus, score identity, and the flat logo accent.
- **Violet Deep** provides the stronger action surface used where white text is required.

### Secondary

- **Cobalt Data** draws the momentum line, positive analysis fills, and selected data emphasis.
- **Placement Blues** step from bright first-place blue through restrained fourth-place blue.

### Tertiary

- **Placement Reds** step from coral fifth place to deep eighth-place red without turning ordinary losses into alarms.
- **Amber State** is reserved for cached-data and availability messages.
- **Red State** is reserved for validation and true error feedback.

### Neutral

- **Ink Deep** is the page ground and deepest plotting surface.
- **Ink Surface** is the standard analytical band and table surface.
- **Ink Raised** supports inputs and primary score fields.
- **Mineral Paper** changes reading mode for the match ledger and onboarding.
- **Primary, Muted, and Secondary Text** provide the content hierarchy.
- **Soft and Strong Rules** divide structure without shadow.

### Named Rules

**The Identity/Data Split Rule.** Violet identifies the product and current selection. Cobalt, stepped blues, and stepped reds encode player data.

**The Paper Is Earned Rule.** Mineral paper appears only where the interface changes reading mode: the match ledger, the insight lead, and onboarding.

**The Honest State Rule.** Cached data, unavailable sources, validation errors, and empty results remain visible and plainly written.

## Typography

**Display Font:** Outfit, with Segoe UI and sans-serif fallbacks.
**Body Font:** Outfit, with Segoe UI and sans-serif fallbacks.
**Label/Mono Font:** Outfit with tabular numerals; no terminal-style mono face is used.

**Character:** Outfit gives the interface a compact, human geometric voice without gaming-font theatrics. Weight and alignment create hierarchy; labels remain sentence case and letter spacing stays neutral.

### Hierarchy

- **Display** (650, 42px, 1.02): First-run identity heading only.
- **Metric** (650, 52-76px, 1): Average placement and Top 4 rate.
- **Title** (650, 20px, 1.1): Analytical bands and view headings.
- **Body** (400, 15px, 1.45): Controls, match detail, and explanatory states.
- **Label** (600, 12px): Form labels, captions, and compact metadata.

### Named Rules

**The Numeral Authority Rule.** Primary statistics are large, tabular, and left aligned. Their labels explain them without competing for attention.

**The Sentence-Case Rule.** Interface labels are sentence case. Uppercase and excessive tracking are not part of the product voice.

## Layout

The desktop shell is capped at 1,560px with 20px side gutters. The masthead uses an asymmetric three-part grid for brand, negative space, and player identity. Controls form one ruled deck beneath it, while sticky tabs sit on the same document axis.

The overview uses a twelve-column field: set performance spans five columns and the match ledger spans seven; momentum spans eight and placement breakdown spans four. These pairs meet edge to edge with one structural rule. Match notes and secondary workflows run full width. Insights use one full-width paper lead, two complete rows of three analysis fields, then one complete row of two.

At 1,100px, paired overview bands stack and comp grids move to two columns. At 720px, analysis becomes one column, the match ledger becomes two rows of ten, and the tab rail scrolls horizontally inside a clipped document boundary. At 440px, filters and player lookup stack.

## Elevation & Depth

The system uses no box shadows. Depth comes from tonal ink layers, the warm paper interruption, one-pixel rules, and content density. Interactive repeated cards lift by two pixels on pointer hover, but their resting state remains flat.

### Named Rules

**The One Edge Rule.** A surface may use a divider or a border, never a border plus a broad shadow.

**The No Glow Rule.** Colored halos, chromatic shadows, shiny accents, and blurred atmosphere do not belong in the application.

## Shapes

Most application structure has square corners. Controls and messages use a restrained 4px radius; repeated comp cards use 6px; the focused onboarding sheet uses 8px. Placement tiles use 2px corners so they read as ledger entries instead of pills. The score alone uses a compact 13px capsule because it is a single short status value.

Hex clipping is reserved for trait breakpoints. The logo uses a crisp open board frame and an ascending review line; it stays flat, geometric, and free of gradients.

## Components

### Buttons

- **Shape:** Compact rectangular control with gently eased corners (4px).
- **Primary:** Violet selection fill, ink text, 40px height, and horizontal 17px padding.
- **Hover / Focus:** A brighter violet tonal shift and a visible three-pixel focus outline.
- **Press:** Immediate scale to 0.97 over 140ms.

### Inputs / Fields

- **Style:** Ink-raised fill, strong-rule border, 4px radius, 40px height.
- **Focus:** Violet border, a restrained translucent three-pixel outline, and an active ink fill.
- **Error / Disabled:** Red text for validation; reduced opacity and progress cursor while loading.

### Navigation

Tabs are text on a ruled rail rather than pills. The active tab uses primary text and a three-pixel violet rule that slides to the selected label over 200ms. The rail stays sticky and becomes horizontally scrollable on mobile. Arrow, Home, and End keys change the selected tab.

### Match Ledger

Twenty compact placement tiles sit on mineral paper, newest first. Each tile uses its exact placement shade, rises four pixels on pointer hover, and reveals a short tooltip containing placement, patch, and active traits.

### Charts

The momentum chart uses one cobalt line and a faint flat area fill on an ink plotting field. Hover draws a vertical inspection rule, emphasizes the nearest point, and opens a mineral tooltip with game placement and estimated momentum. The canvas redraws at its displayed width for mobile legibility.

### Trait Breakpoints

Trait activation tiers use a true hex silhouette because the geometry is native to TFT's trait language. Bronze, silver, gold, prismatic, and active fills are restricted to this component.

### Repeated Comp Cards

Comp records use the only recurring card shell: a 6px radius, one soft border, and ink-raised fill. Internal statistics are aligned as a ruled four-column row. Hover changes tone and position without adding shadow.

### Loading And First Run

Refresh preserves the existing dashboard and lowers its opacity instead of blanking the page. The first-run screen uses a centered mineral sheet with an inline Riot ID field, clear validation, and the same flat logo system.

## Do's and Don'ts

### Do:

- **Do** use editorial bands and rules to organize primary analysis.
- **Do** let important performance numerals occupy open space.
- **Do** reserve mineral paper for meaningful changes in reading mode.
- **Do** preserve exact blue and red placement semantics across views.
- **Do** keep controls native, compact, keyboard accessible, and visibly focused.
- **Do** use 140-220ms motion for state, orientation, and feedback.
- **Do** label cached, unavailable, and incomplete data honestly.

### Don't:

- **Don't** rebuild the page as a uniform grid of rounded cards.
- **Don't** use glow, glossy gradients, glass, purple atmosphere, or shiny borders.
- **Don't** turn metadata, tags, or scope values into clouds of pills.
- **Don't** use gaming fonts, neon cyberpunk styling, or Discord-bot visual language.
- **Don't** use hexagons outside trait and board-specific contexts.
- **Don't** add ambient motion, decorative floating, or long page transitions.
- **Don't** invent recommendations, global comparisons, or statistics the data does not provide.

