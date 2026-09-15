# TFT Tracker — Project Vision & Roadmap

## What It Is

TFT Tracker is a **data analysis web app** for Teamfight Tactics players.

It is **not** a meta site. It does not tell you what to play, what comps are best, or what augments to pick. It is a pure data visualization tool — it shows you your own data in as many ways as possible and lets you draw your own conclusions.

---

## Core Philosophy

- **No recommendations.** The app displays data. The player interprets it.
- **Personal first.** Every stat is about the user's own games.
- **Comparison second.** Once personal data is shown, the user can optionally compare it to the global playerbase or a specific Elo range.
- **Filter everything.** Data should be filterable by patch, time range, game mode, and Elo bracket.

---

## Target User

TFT players who want to understand their own gameplay through data — not be told what to do. Especially useful for higher Elo players who make fewer mistakes and want granular insight into their tendencies and patterns.

---

## Features

### Phase 1 - Personal Dashboard (MVP Complete)
Built using the Riot Games API.

- [x] Average placement (last N games)
- [x] Top 4 rate
- [x] Placement trend graph over time
- [x] Most played units
- [x] Most played traits
- [x] Placement breakdown (how many 1sts, 2nds, 3rds... 8ths)
- [x] Performance per unit (avg placement when unit is played)
- [x] Performance per trait (avg placement when trait is active)
- [x] Most played comps (matched to TFTAcademy final units)
- [x] Filter by patch
- [x] Filter by game count / current set
- [x] First-run Riot ID setup with local persistence
- [x] Recent games visualization
- [x] Trait breakpoint visualization
- [x] TFTAcademy comp performance tab

### Phase 2 — Advanced Personal Stats
Requires Overwolf API access.

- [ ] Augment pick history
- [ ] Performance per augment (avg placement, top 4 rate)
- [ ] Augment combo analysis (which augments are picked together and how they perform)
- [ ] Scouting time vs top 4 rate correlation
- [ ] Economy tendencies (when user levels, when user rolls)
- [ ] Round-by-round board data

### Phase 3 — Global Playerbase Comparison
Requires Overwolf partner API or data partnership.

- [ ] Compare personal augment performance to global playerbase
- [ ] Compare personal unit performance to global playerbase
- [ ] Filter global data by Elo bracket (e.g. Diamond+, Master+)
- [ ] Visual indicator of personal vs global (e.g. color coding: green = better than average, red = worse)
- [ ] Per-patch global data so comparisons are patch-accurate

### Phase 4 — Web App
- [ ] User login via Riot account (OAuth)
- [ ] Cloud database to store match history beyond API limits (20 game cap)
- [ ] Historical data across all sets / patches
- [ ] Public profiles
- [ ] Mobile responsive design

---

## Data Visualization Goals

- Numbers and percentages for all stats
- Line graphs for trends over time
- Bar charts for distributions (placement breakdown, unit frequency)
- Filters: patch, time range, Elo bracket, game mode
- Side-by-side personal vs global comparison views

---

## Tech Stack

### Current
- Python 3.11
- Riot Games API
- Flask (backend)
- HTML / CSS / JavaScript (frontend)
- matplotlib (charts, temporary)

### Planned
- Overwolf Game Events API (live + historical data)
- React or Vue (frontend, when scaling)
- PostgreSQL or MongoDB (persistent data storage)
- Deployed on Railway, Vercel, or AWS

---

## Data Sources

| Source | Access | Status |
|---|---|---|
| Riot Games API | Free dev key | ✅ Active |
| Overwolf Game Events API | Partner approval required | 🟡 Applied |
| Global playerbase data | Overwolf partner or data deal | ⏳ Pending |

---

## Known Limitations (Current)

- Riot API limits match history to the last 200 games
- Augment data is not available via Riot API (Riot ToS restriction)
- No persistent storage yet — data lives in a local cache file
- No user authentication — currently hardcoded to one player

---

## Differentiator

Unlike MetaTFT, TFT Academy, tactics.tools, and LOLChess:

> TFT Tracker does not tell you what to play. It shows you what you have played and how it performed — then gets out of the way.

