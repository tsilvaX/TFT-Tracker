# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The product is primarily for the owner's personal Teamfight Tactics review workflow, with the interface and analysis quality aimed at serious TFT players who want to understand their own match history, performance patterns, and tendencies.

## Product Purpose

TFT Tracker analyzes and visualizes a player's own Teamfight Tactics data. It exists to make personal performance easier to inspect through match history, placement trends, unit and trait usage, comp patterns, and related statistics.

Success means the player can review what they have actually played and how it performed without being pushed toward a recommended meta choice.

## Positioning

TFT Tracker is a personal dashboard, not a meta guide. It should preserve both of these commitments:

- Personal performance and pattern analysis comes first.
- The app does not recommend what to play, what comps are best, or what augments to pick.

Comparison features can come later, but they should be secondary to the player's own data and must be based on real retrieved or reliably calculated data.

## Operating Context

The current product is a local Flask web app backed by Python data processing. It uses Riot Games API data, local cache files, and a single HTML/CSS/JavaScript template to show dashboard views.

Current workflows include entering or persisting a Riot ID, loading recent TFT match data, filtering by patch or match count, viewing recent games, inspecting placement and trend stats, reviewing unit and trait performance, and matching personal games against TFTAcademy comp unit lists.

## Capabilities and Constraints

Current capabilities evidenced in the codebase include:

- Riot ID lookup and local player persistence.
- Average placement and Top 4 rate.
- Placement trend and placement breakdown.
- Recent game visualization.
- Most played units and traits.
- Unit, trait, and trait-breakpoint performance.
- Personal tags and generated performance insights.
- TFTAcademy comp ingestion and personal comp-match performance analysis.
- Filters for patch, current set, and match count.

Durable constraints:

- Riot API limits and payload availability must be respected.
- The app should only show data it can retrieve or calculate reliably.
- Future work must not fabricate player data, global comparisons, testimonials, proof, partnerships, or benchmarks.
- Augment and deeper round-by-round analysis remain constrained by available data sources and Overwolf access.
- Persistent cloud storage, authentication, public profiles, and global comparison are planned directions, not current product facts.

## Brand Commitments

The product name is TFT Tracker. The voice should stay direct, analytical, and player-centered. Existing assets include the tracker mark at `static/assets/tft_tracker_mark.svg` and `static/assets/tft_tracker_mark.png`.

## Evidence on Hand

Real project evidence includes:

- `README.md`
- `TFT TRACKER VISION.md`
- `app.py`
- `tft_tracker.py`
- `templates/index.html`
- cached Riot/TFTAcademy/Data Dragon data in `cache/`
- local API/cache files used by the current development workflow
- tracker mark assets in `static/assets/`

No verified global playerbase dataset, Overwolf partner data, production deployment, public user accounts, testimonials, benchmarks, or external proof claims are present in the repository.

## Product Principles

- Show the player's own data first.
- Explain patterns through visualization and calculated stats, not prescriptive recommendations.
- Keep every claim traceable to retrieved, cached, or locally calculated data.
- Treat comparison as optional context after personal performance is clear.
- Preserve serious-player depth while keeping the product useful for the owner's local workflow.
