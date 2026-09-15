from collections import Counter, defaultdict
from pathlib import Path
import json
import os
import re
import threading
import time
from urllib.parse import quote

import requests
from dotenv import load_dotenv


load_dotenv()

DEFAULT_PUUID = os.getenv(
    "TFT_PUUID",
    "IYA-33ZGOldH7GZ9TEmfSuNABYRgmT2jx7cEVt7QbbHPvFzpmoU9Pe05M4ZdPJUONms4dMj5JSyPKQ",
)
DEFAULT_RIOT_ID = os.getenv("TFT_RIOT_ID", "Thorns#ESP")
CACHE_PATH = Path("local_api.json")
CACHE_DIR = Path("cache")
COMPS_CACHE_PATH = CACHE_DIR / "tftacademy_comps.json"
TACTICIANS_CACHE_PATH = CACHE_DIR / "ddragon_tacticians.json"
DEFAULT_MATCH_COUNT = 200
TFTACADEMY_COMPS_URL = "https://tftacademy.com/tierlist/comps"
DDRAGON_VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
_MATCH_LOAD_LOCKS = defaultdict(threading.Lock)


def resolve_riot_id(riot_id):
    """Resolve a Riot ID like Thorns#ESP into account data with a PUUID."""
    game_name, tag_line = _parse_riot_id(riot_id)

    response = _riot_get(
        (
            "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
            f"{quote(game_name)}/{quote(tag_line)}"
        )
    )
    return response.json()


def _resolve_account_with_local_fallback(riot_id):
    try:
        return resolve_riot_id(riot_id)
    except requests.RequestException:
        if riot_id.strip().casefold() != DEFAULT_RIOT_ID.casefold():
            raise

        game_name, tag_line = _parse_riot_id(DEFAULT_RIOT_ID)
        return {
            "puuid": DEFAULT_PUUID,
            "gameName": game_name,
            "tagLine": tag_line,
        }


def load_matches(cache_path=None, puuid=DEFAULT_PUUID, refresh=False, match_count=DEFAULT_MATCH_COUNT):
    cache_path = Path(cache_path) if cache_path else _cache_path_for_puuid(puuid)

    with _MATCH_LOAD_LOCKS[str(cache_path)]:
        return _load_matches_locked(
            cache_path=cache_path,
            puuid=puuid,
            refresh=refresh,
            match_count=match_count,
        )


def _load_matches_locked(cache_path=None, puuid=DEFAULT_PUUID, refresh=False, match_count=DEFAULT_MATCH_COUNT):
    """Load cached matches, refreshing when Riot has newer match IDs."""
    cache_path = Path(cache_path) if cache_path else _cache_path_for_puuid(puuid)
    match_count = int(match_count or DEFAULT_MATCH_COUNT)

    cached_matches = []
    if cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as file:
            cached_matches = json.load(file)

        if cached_matches and not refresh and len(cached_matches) >= match_count:
            try:
                if _cache_has_latest_match(cached_matches, puuid):
                    return cached_matches
            except requests.RequestException:
                return cached_matches

    requested_count = max(match_count, len(cached_matches))

    try:
        match_ids_response = _riot_get(
            (
                "https://americas.api.riotgames.com/tft/match/v1/matches/by-puuid/"
                f"{puuid}/ids?count={requested_count}"
            )
        )
    except requests.RequestException:
        if cached_matches and not refresh:
            return cached_matches
        raise
    match_ids = match_ids_response.json()
    cached_by_id = {
        match.get("metadata", {}).get("match_id"): match
        for match in cached_matches
        if match.get("metadata", {}).get("match_id")
    }

    matches = []
    for index, match_id in enumerate(match_ids, start=1):
        if match_id in cached_by_id:
            matches.append(cached_by_id[match_id])
            continue

        match_response = _riot_get(
            f"https://americas.api.riotgames.com/tft/match/v1/matches/{match_id}"
        )
        print(f"{index} / {len(match_ids)}")
        matches.append(match_response.json())
        time.sleep(0.25)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as file:
        json.dump(matches, file)

    return matches


def _riot_get(url, **kwargs):
    timeout = kwargs.pop("timeout", 20)
    response = requests.get(
        url,
        headers=_riot_headers(),
        timeout=timeout,
        **kwargs,
    )

    if response.status_code == 429:
        retry_after = float(response.headers.get("Retry-After") or 2)
        time.sleep(retry_after)
        response = requests.get(
            url,
            headers=_riot_headers(),
            timeout=timeout,
            **kwargs,
        )

    response.raise_for_status()
    return response


def _cache_has_latest_match(cached_matches, puuid):
    newest_cached_id = (
        cached_matches[0]
        .get("metadata", {})
        .get("match_id")
    ) if cached_matches else None

    if not newest_cached_id:
        return False

    latest_response = _riot_get(
        (
            "https://americas.api.riotgames.com/tft/match/v1/matches/by-puuid/"
            f"{puuid}/ids?count=1"
        )
    )
    latest_ids = latest_response.json()
    return bool(latest_ids) and latest_ids[0] == newest_cached_id


def get_player_entries(matches, puuid=DEFAULT_PUUID):
    """Flatten the user's participant rows into one record per match."""
    entries = []

    for match in matches:
        info = match.get("info", {})
        participant = _find_participant(info.get("participants", []), puuid)

        if not participant:
            continue

        entries.append(
            _entry_from_match(match, info, participant)
        )

    return sorted(entries, key=lambda entry: entry.get("game_datetime") or 0)


def _entry_from_match(match, info, participant):
    set_number = info.get("tft_set_number")
    companion = participant.get("companion") or {}

    return {
        "match_id": match.get("metadata", {}).get("match_id"),
        "game_datetime": info.get("game_datetime"),
        "game_version": info.get("game_version", ""),
        "patch": _extract_patch(info.get("game_version", ""), set_number),
        "queue_id": info.get("queue_id"),
        "tft_set_number": set_number,
        "placement": participant.get("placement"),
        "level": participant.get("level"),
        "gold_left": participant.get("gold_left"),
        "last_round": participant.get("last_round"),
        "players_eliminated": participant.get("players_eliminated"),
        "total_damage_to_players": participant.get("total_damage_to_players"),
        "augments": [_clean_tft_name(augment) for augment in participant.get("augments", [])],
        "tactician": _tactician_id(companion),
        "tactician_content_id": companion.get("content_ID"),
        "units": [_clean_tft_name(unit.get("character_id", "")) for unit in participant.get("units", [])],
        "traits": [
            {
                "name": _clean_tft_name(trait.get("name", "")),
                "num_units": trait.get("num_units", 0),
                "tier_current": trait.get("tier_current", 0),
                "style": trait.get("style", 0),
            }
            for trait in participant.get("traits", [])
            if _is_active_trait(trait)
        ],
    }


def calculate_dashboard_stats(
    matches=None,
    puuid=DEFAULT_PUUID,
    riot_id=None,
    set_number=None,
    patch=None,
    limit=None,
    match_count=DEFAULT_MATCH_COUNT,
    current_only=False,
    refresh=False,
):
    """Calculate the current Phase 1 dashboard from Riot match data."""
    player = {
        "puuid": puuid,
        "riot_id": riot_id or DEFAULT_RIOT_ID,
        "game_name": None,
        "tag_line": None,
    }

    if riot_id:
        account = _resolve_account_with_local_fallback(riot_id)
        puuid = account["puuid"]
        player = {
            "puuid": puuid,
            "riot_id": f"{account.get('gameName')}#{account.get('tagLine')}",
            "game_name": account.get("gameName"),
            "tag_line": account.get("tagLine"),
        }

    if matches is None:
        matches = load_matches(
            cache_path=None,
            puuid=puuid,
            refresh=refresh,
            match_count=match_count,
        )

    entries = get_player_entries(matches, puuid)
    all_entries = entries[:]
    favorite_tactician = _favorite_tactician(all_entries, sample_limit=50)
    scope = _resolve_match_scope(entries, set_number=set_number, patch=patch, current_only=current_only)
    entries = scope["entries"]
    set_entries = scope["set_entries"]

    if limit:
        entries = entries[-int(limit) :]

    placements = [entry["placement"] for entry in entries if entry.get("placement")]
    match_total = len(placements)

    if not placements:
        return {
            "player": player,
            "match_total": 0,
            "avg_placement": None,
            "top4_rate": None,
            "augment_stats": _augment_stats({}, False),
            "favorite_tactician": favorite_tactician,
            "current_set": scope["selected_set"],
            "current_patch": scope["selected_patch"],
            "latest_set": scope["latest_set"],
            "latest_patch": scope["latest_patch"],
            "available_sets": _available_sets(all_entries),
            "available_patches": _available_patches(all_entries, scope["selected_set"]),
            "performance_score": _performance_score(set_entries),
            "placement_breakdown": {str(place): 0 for place in range(1, 9)},
            "placement_trend": [],
            "recent_matches": [],
            "recent_summary": _recent_summary([]),
            "player_tags": [],
            "insights": _personal_insights([], {}, {}, {}),
            "data_scope": _data_scope(entries, scope, all_entries),
            "most_played_units": [],
            "most_played_traits": [],
            "trait_breakpoints": [],
            "unit_performance": [],
            "trait_performance": [],
            "most_played_comps": [],
        }

    unit_counter = Counter()
    trait_counter = Counter()
    unit_results = defaultdict(list)
    trait_results = defaultdict(list)
    trait_breakpoint_results = defaultdict(list)
    comp_results = defaultdict(list)
    augment_results = defaultdict(list)
    saw_augment_data = False

    for entry in entries:
        placement = entry["placement"]
        units = set(entry["units"])
        traits = {trait["name"] for trait in entry["traits"]}
        comp_key = " / ".join(sorted(traits)) if traits else "No active traits"
        unit_counter.update(units)
        trait_counter.update(traits)
        comp_results[comp_key].append(placement)

        if entry["augments"]:
            saw_augment_data = True

            for augment in entry["augments"]:
                augment_results[augment].append(placement)

        for unit in units:
            unit_results[unit].append(placement)

        for trait in traits:
            trait_results[trait].append(placement)

        for trait in entry["traits"]:
            key = (trait["name"], trait.get("num_units") or 0, trait.get("style") or 0)
            trait_breakpoint_results[key].append(placement)

    return {
        "player": player,
        "match_total": match_total,
        "avg_placement": round(sum(placements) / match_total, 2),
        "top4_rate": round(_top4_rate(placements), 2),
        "augment_stats": _augment_stats(augment_results, saw_augment_data),
        "favorite_tactician": favorite_tactician,
        "current_set": scope["selected_set"],
        "current_patch": scope["selected_patch"],
        "latest_set": scope["latest_set"],
        "latest_patch": scope["latest_patch"],
        "available_sets": _available_sets(all_entries),
        "available_patches": _available_patches(all_entries, scope["selected_set"]),
        "performance_score": _performance_score(set_entries),
        "placement_breakdown": _placement_breakdown(placements),
        "placement_trend": [
            {
                "match_id": entry["match_id"],
                "game_datetime": entry["game_datetime"],
                "patch": entry["patch"],
                "placement": entry["placement"],
            }
            for entry in entries
        ],
        "recent_matches": _recent_matches(entries, count=20),
        "recent_summary": _recent_summary(entries[-20:]),
        "player_tags": _player_tags(entries, unit_counter, trait_counter, comp_results),
        "insights": _personal_insights(entries, unit_results, trait_results, comp_results),
        "data_scope": _data_scope(entries, scope, all_entries),
        "most_played_units": _counter_rows(unit_counter),
        "most_played_traits": _counter_rows(trait_counter),
        "trait_breakpoints": _trait_breakpoint_rows(trait_breakpoint_results),
        "unit_performance": _performance_rows(unit_results),
        "trait_performance": _performance_rows(trait_results),
        "most_played_comps": _performance_rows(comp_results, name_key="traits"),
    }


def analyze_selection(
    riot_id,
    units=None,
    traits=None,
    comp_units=None,
    set_number=None,
    patch=None,
    match_count=DEFAULT_MATCH_COUNT,
):
    units = {_normalize_name(unit) for unit in units or [] if unit}
    traits = {_normalize_name(trait) for trait in traits or [] if trait}
    comp_units = {_normalize_name(unit) for unit in comp_units or [] if unit}
    selected_units = units | comp_units

    stats = calculate_dashboard_stats(
        riot_id=riot_id,
        set_number=set_number,
        patch=patch,
        match_count=match_count,
        current_only=False,
    )
    matches = load_matches(puuid=stats["player"]["puuid"], match_count=match_count)
    entries = get_player_entries(matches, stats["player"]["puuid"])
    scope = _resolve_match_scope(entries, set_number=set_number, patch=patch)
    entries = scope["entries"]
    matched_entries = []

    for entry in entries:
        entry_units = {_normalize_name(unit) for unit in entry["units"]}
        entry_traits = {_normalize_name(trait["name"]) for trait in entry["traits"]}

        if selected_units and not selected_units.issubset(entry_units):
            continue

        if traits and not traits.issubset(entry_traits):
            continue

        matched_entries.append(entry)

    placements = [entry["placement"] for entry in matched_entries if entry.get("placement")]

    if not placements:
        return {
            "games": 0,
            "avg_placement": None,
            "top4_rate": None,
            "win_rate": None,
            "placement_breakdown": _placement_breakdown([]),
            "matches": [],
        }

    return {
        "games": len(placements),
        "avg_placement": round(sum(placements) / len(placements), 2),
        "top4_rate": round(_top4_rate(placements), 2),
        "win_rate": round((sum(1 for placement in placements if placement == 1) / len(placements)) * 100, 2),
        "placement_breakdown": _placement_breakdown(placements),
        "matches": [
            {
                "match_id": entry["match_id"],
                "placement": entry["placement"],
                "patch": entry["patch"],
                "units": entry["units"],
                "traits": [trait["name"] for trait in entry["traits"]],
            }
            for entry in matched_entries[-20:]
        ],
    }


def calculate_tftacademy_comp_performance(
    riot_id,
    set_number=None,
    patch=None,
    limit=None,
    match_count=DEFAULT_MATCH_COUNT,
    current_only=False,
    refresh_comps=False,
):
    account = _resolve_account_with_local_fallback(riot_id)
    puuid = account["puuid"]
    matches = load_matches(puuid=puuid, match_count=match_count)
    entries = get_player_entries(matches, puuid)
    all_entries = entries[:]
    scope = _resolve_match_scope(entries, set_number=set_number, patch=patch, current_only=current_only)
    entries = scope["entries"]

    if limit:
        entries = entries[-int(limit) :]

    comps_payload = get_tftacademy_comps(refresh=refresh_comps)
    comps = comps_payload.get("comps", [])
    rows = []

    for comp in comps:
        matches_for_comp = []

        for entry in entries:
            match_result = _match_comp_units(comp.get("units", []), entry.get("units", []))

            if match_result:
                matches_for_comp.append({
                    **match_result,
                    "game_datetime": entry.get("game_datetime"),
                    "placement": entry.get("placement"),
                    "patch": entry.get("patch"),
                    "match_id": entry.get("match_id"),
                })

        placements = [match["placement"] for match in matches_for_comp if match.get("placement")]
        rows.append(_academy_comp_row(comp, matches_for_comp, placements))

    return {
        "source": comps_payload.get("source", TFTACADEMY_COMPS_URL),
        "player": {
            "puuid": puuid,
            "riot_id": f"{account.get('gameName')}#{account.get('tagLine')}",
            "game_name": account.get("gameName"),
            "tag_line": account.get("tagLine"),
        },
        "data_scope": _data_scope(entries, scope, all_entries),
        "comps": sorted(rows, key=_academy_comp_sort_key),
    }


def get_tftacademy_comps(refresh=False):
    if COMPS_CACHE_PATH.exists() and not refresh:
        with COMPS_CACHE_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)

    response = requests.get(TFTACADEMY_COMPS_URL, timeout=20)
    response.raise_for_status()
    html = response.text
    comps = _parse_tftacademy_comps(html)
    payload = {
        "source": TFTACADEMY_COMPS_URL,
        "comps": comps,
    }

    COMPS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with COMPS_CACHE_PATH.open("w", encoding="utf-8") as file:
        json.dump(payload, file)

    return payload


def get_avg_placement():
    stats = calculate_dashboard_stats()
    return stats["avg_placement"] or 0


def get_stats():
    stats = calculate_dashboard_stats()
    return stats["top4_rate"] or 0


def _find_participant(participants, puuid):
    return next(
        (participant for participant in participants if participant.get("puuid") == puuid),
        None,
    )


def _riot_headers():
    load_dotenv(override=True)
    api_key = os.getenv("API_KEY")

    if not api_key:
        raise RuntimeError("Missing API_KEY in .env; cannot fetch Riot API data.")

    return {"X-Riot-Token": api_key}


def _parse_riot_id(riot_id):
    if not riot_id or "#" not in riot_id:
        raise ValueError("Enter a Riot ID in the format GameName#TAG.")

    game_name, tag_line = [part.strip() for part in riot_id.split("#", 1)]

    if not game_name or not tag_line:
        raise ValueError("Enter a Riot ID in the format GameName#TAG.")

    return game_name, tag_line


def _cache_path_for_puuid(puuid):
    safe_puuid = re.sub(r"[^A-Za-z0-9_-]", "_", puuid)
    return CACHE_DIR / f"{safe_puuid}.json"


def _clean_tft_name(name):
    name = name or ""
    name = re.sub(r"^TFT\d+_", "", name)
    name = re.sub(r"^DA_(?:18_)?", "", name)
    name = re.sub(r"(?<=[A-Za-z])18(?=_|$)", "", name)
    name = re.sub(r"18$", "", name)
    name = re.sub(r"UniqueTrait$", "", name)
    name = re.sub(r"Trait$", "", name)
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    name = name.replace("_", " ")
    return " ".join(name.split()) or "Unknown"


def _normalize_name(name):
    normalized = _clean_tft_name(name).lower()
    return re.sub(r"[^a-z0-9]+", "", normalized)


def _format_tactician(companion):
    if not companion:
        return None

    item_id = companion.get("item_ID")
    skin_id = companion.get("skin_ID")
    species = _clean_tft_name(companion.get("species", ""))

    if species and species != "Unknown":
        return species

    if item_id is None:
        return None

    if skin_id:
        return f"Tactician {item_id}-{skin_id}"

    return f"Tactician {item_id}"


def _tactician_id(companion):
    if not companion or companion.get("item_ID") is None:
        return None

    return str(companion.get("item_ID"))


def _extract_patch(game_version, set_number=None):
    match = re.search(r"Version\s+(\d+\.\d+)", game_version or "")
    if match:
        return match.group(1)

    if set_number == _current_tft_set():
        return _current_tft_patch()

    return "Unknown"


def _is_active_trait(trait):
    return trait.get("tier_current", 0) > 0 or trait.get("style", 0) > 0


def _top4_rate(placements):
    return (sum(1 for placement in placements if placement <= 4) / len(placements)) * 100


def _placement_breakdown(placements):
    counts = Counter(placements)
    return {str(place): counts.get(place, 0) for place in range(1, 9)}


def _counter_rows(counter, limit=12):
    return [
        {"name": name, "games": games}
        for name, games in counter.most_common(limit)
    ]


def _recent_matches(entries, count=20):
    rows = []

    for entry in reversed(entries[-count:]):
        traits = sorted(
            entry.get("traits", []),
            key=lambda trait: (
                trait.get("style") or 0,
                trait.get("num_units") or 0,
                trait.get("name") or "",
            ),
            reverse=True,
        )
        rows.append(
            {
                "match_id": entry.get("match_id"),
                "game_datetime": entry.get("game_datetime"),
                "patch": entry.get("patch"),
                "placement": entry.get("placement"),
                "level": entry.get("level"),
                "gold_left": entry.get("gold_left"),
                "last_round": entry.get("last_round"),
                "players_eliminated": entry.get("players_eliminated"),
                "total_damage_to_players": entry.get("total_damage_to_players"),
                "units": entry.get("units", [])[:10],
                "traits": [
                    {
                        "name": trait.get("name"),
                        "num_units": trait.get("num_units") or 0,
                        "tier_current": trait.get("tier_current") or 0,
                        "style": trait.get("style") or 0,
                    }
                    for trait in traits[:6]
                ],
            }
        )

    return rows


def _recent_summary(entries):
    placements = [entry["placement"] for entry in entries if entry.get("placement")]

    if not placements:
        return {
            "games": 0,
            "avg_placement": None,
            "top4_count": 0,
            "wins": 0,
            "top4_rate": None,
            "avg_level": None,
            "avg_damage": None,
            "avg_eliminated": None,
            "avg_gold_left": None,
        }

    return {
        "games": len(placements),
        "avg_placement": round(sum(placements) / len(placements), 2),
        "top4_count": sum(1 for placement in placements if placement <= 4),
        "wins": sum(1 for placement in placements if placement == 1),
        "top4_rate": round(_top4_rate(placements), 2),
        "avg_level": _average_entry_value(entries, "level"),
        "avg_damage": _average_entry_value(entries, "total_damage_to_players"),
        "avg_eliminated": _average_entry_value(entries, "players_eliminated"),
        "avg_gold_left": _average_entry_value(entries, "gold_left"),
    }


def _average_entry_value(entries, key):
    values = [
        entry[key]
        for entry in entries
        if isinstance(entry.get(key), (int, float)) and entry.get(key) > 0
    ]

    if not values:
        return None

    return round(sum(values) / len(values), 2)


def _player_tags(entries, unit_counter, trait_counter, comp_results):
    if not entries:
        return []

    placements = [entry["placement"] for entry in entries if entry.get("placement")]
    recent = entries[-20:]
    recent_placements = [entry["placement"] for entry in recent if entry.get("placement")]
    tags = []

    if recent_placements:
        recent_avg = sum(recent_placements) / len(recent_placements)
        recent_top4 = _top4_rate(recent_placements)
        if recent_avg <= 3.75:
            tags.append(_tag("Climbing Form", "positive", f"Last 20 avg place {recent_avg:.2f}."))
        elif recent_avg >= 4.75:
            tags.append(_tag("Review Window", "warning", f"Last 20 avg place {recent_avg:.2f}."))

        last_five = recent_placements[-5:]
        if len(last_five) >= 5 and all(placement > 4 for placement in last_five):
            tags.append(_tag("Cold Streak", "warning", "Last five games missed Top 4."))
        elif len(last_five) >= 5 and sum(1 for placement in last_five if placement <= 4) >= 4:
            tags.append(_tag("Hot Streak", "positive", "Four of last five games were Top 4."))

        if recent_top4 >= 60:
            tags.append(_tag("Stable Top 4", "positive", f"Last 20 Top 4 rate {recent_top4:.0f}%."))
        elif recent_top4 <= 40:
            tags.append(_tag("Consistency Leak", "warning", f"Last 20 Top 4 rate {recent_top4:.0f}%."))

    if placements:
        win_rate = (sum(1 for placement in placements if placement == 1) / len(placements)) * 100
        top4_rate = _top4_rate(placements)

        if top4_rate >= 55 and win_rate < 12:
            tags.append(_tag("Needs Closing", "neutral", "Top 4s are landing more often than wins."))

    if entries:
        avg_eliminated = _average_entry_value(entries, "players_eliminated")
        avg_gold_left = _average_entry_value(entries, "gold_left")
        avg_damage = _average_entry_value(entries, "total_damage_to_players")

        if avg_eliminated is not None and avg_eliminated < 0.8:
            tags.append(_tag("Low Elims", "neutral", f"Avg eliminations {avg_eliminated}."))

        if avg_gold_left is not None and avg_gold_left >= 14:
            tags.append(_tag("Gold Saver", "neutral", f"Avg gold left {avg_gold_left}."))

        if avg_damage is not None and avg_damage < 65:
            tags.append(_tag("Low Damage", "warning", f"Avg player damage {avg_damage}."))

    if comp_results:
        top_comp, top_comp_placements = max(comp_results.items(), key=lambda item: len(item[1]))
        top_comp_share = len(top_comp_placements) / max(len(entries), 1)
        if top_comp_share >= 0.28:
            tags.append(_tag("Forcer", "neutral", f"Most repeated trait shell appears in {top_comp_share:.0%} of games."))
        else:
            tags.append(_tag("Flexible", "positive", "No single trait shell dominates your history."))

    if trait_counter:
        trait, games = trait_counter.most_common(1)[0]
        share = games / max(len(entries), 1)
        if share >= 0.25:
            tags.append(_tag(f"{trait} Main", "neutral", f"Appears in {share:.0%} of games."))

    if unit_counter:
        unit, games = unit_counter.most_common(1)[0]
        share = games / max(len(entries), 1)
        if share >= 0.25:
            tags.append(_tag(f"{unit} Regular", "neutral", f"Played in {share:.0%} of games."))

    deduped = []
    seen = set()
    for tag in tags:
        if tag["label"] not in seen:
            deduped.append(tag)
            seen.add(tag["label"])

    return deduped[:8]


def _personal_insights(entries, unit_results, trait_results, comp_results):
    placements = [entry["placement"] for entry in entries if entry.get("placement")]
    recent_placements = [entry["placement"] for entry in entries[-20:] if entry.get("placement")]

    return {
        "form": _form_insight(placements, recent_placements),
        "streaks": _streak_insight(placements),
        "placement_bands": _placement_band_insight(placements),
        "patch_samples": _patch_insights(entries),
        "economy": _economy_insight(entries),
        "best_units": _extreme_performance(unit_results, direction="best"),
        "review_units": _extreme_performance(unit_results, direction="worst"),
        "best_traits": _extreme_performance(trait_results, direction="best"),
        "review_traits": _extreme_performance(trait_results, direction="worst"),
        "trait_shells": _extreme_performance(comp_results, direction="most_played", limit=4),
    }


def _streak_insight(placements):
    if not placements:
        return {
            "current_label": "No streak data",
            "current_length": 0,
            "best_top4": 0,
            "worst_bot4": 0,
        }

    current_type = "Top 4" if placements[-1] <= 4 else "Bot 4"
    current_length = 0
    best_top4 = 0
    worst_bot4 = 0
    top4_run = 0
    bot4_run = 0

    for placement in placements:
        if placement <= 4:
            top4_run += 1
            bot4_run = 0
        else:
            bot4_run += 1
            top4_run = 0

        best_top4 = max(best_top4, top4_run)
        worst_bot4 = max(worst_bot4, bot4_run)

    for placement in reversed(placements):
        if (placement <= 4 and current_type == "Top 4") or (placement > 4 and current_type == "Bot 4"):
            current_length += 1
        else:
            break

    return {
        "current_label": f"{current_type} streak",
        "current_length": current_length,
        "best_top4": best_top4,
        "worst_bot4": worst_bot4,
    }


def _placement_band_insight(placements):
    if not placements:
        return []

    total = len(placements)
    bands = [
        ("Wins", lambda placement: placement == 1),
        ("Top 2", lambda placement: placement <= 2),
        ("Top 4", lambda placement: placement <= 4),
        ("5th/6th", lambda placement: placement in (5, 6)),
        ("7th/8th", lambda placement: placement in (7, 8)),
    ]

    return [
        {
            "label": label,
            "games": count,
            "rate": round((count / total) * 100, 2),
        }
        for label, predicate in bands
        for count in [sum(1 for placement in placements if predicate(placement))]
    ]


def _patch_insights(entries, min_games=3, limit=6):
    patch_results = defaultdict(list)

    for entry in entries:
        if entry.get("patch") and entry.get("placement"):
            patch_results[entry["patch"]].append(entry["placement"])

    rows = []
    for patch, placements in patch_results.items():
        if len(placements) < min_games:
            continue

        rows.append(
            {
                "patch": patch,
                "games": len(placements),
                "avg_placement": round(sum(placements) / len(placements), 2),
                "top4_rate": round(_top4_rate(placements), 2),
            }
        )

    return sorted(rows, key=lambda row: (-row["games"], row["avg_placement"]))[:limit]


def _economy_insight(entries):
    recent = entries[-20:]

    return {
        "recent_avg_level": _average_entry_value(recent, "level"),
        "recent_avg_gold_left": _average_entry_value(recent, "gold_left"),
        "overall_avg_level": _average_entry_value(entries, "level"),
        "overall_avg_gold_left": _average_entry_value(entries, "gold_left"),
    }


def _form_insight(placements, recent_placements):
    if not placements or not recent_placements:
        return {
            "label": "No form data",
            "tone": "neutral",
            "overall_avg": None,
            "recent_avg": None,
            "delta": None,
        }

    overall_avg = sum(placements) / len(placements)
    recent_avg = sum(recent_placements) / len(recent_placements)
    delta = recent_avg - overall_avg

    if delta <= -0.35:
        label = "Recent form is above your baseline"
        tone = "positive"
    elif delta >= 0.35:
        label = "Recent form is below your baseline"
        tone = "warning"
    else:
        label = "Recent form matches your baseline"
        tone = "neutral"

    return {
        "label": label,
        "tone": tone,
        "overall_avg": round(overall_avg, 2),
        "recent_avg": round(recent_avg, 2),
        "delta": round(delta, 2),
    }


def _extreme_performance(results, direction="best", limit=5, min_games=5):
    rows = []

    for name, placements in results.items():
        if len(placements) < min_games:
            continue

        rows.append(
            {
                "name": name,
                "games": len(placements),
                "avg_placement": round(sum(placements) / len(placements), 2),
                "top4_rate": round(_top4_rate(placements), 2),
            }
        )

    if direction == "best":
        return sorted(rows, key=lambda row: (row["avg_placement"], -row["games"]))[:limit]

    if direction == "worst":
        return sorted(rows, key=lambda row: (-row["avg_placement"], -row["games"]))[:limit]

    return sorted(rows, key=lambda row: (-row["games"], row["avg_placement"]))[:limit]


def _resolve_match_scope(entries, set_number=None, patch=None, current_only=False):
    available_sets = _available_sets(entries)
    latest_set = _latest_value(entries, "tft_set_number")
    selected_set = _parse_set_filter(set_number)

    if selected_set is None:
        selected_set = latest_set

    if current_only and selected_set is None:
        selected_set = latest_set

    set_entries = [
        entry
        for entry in entries
        if selected_set is None or entry.get("tft_set_number") == selected_set
    ]
    latest_patch = _latest_value(set_entries, "patch")
    selected_patch = patch or "latest"

    if selected_patch == "latest":
        selected_patch = latest_patch

    scoped_entries = set_entries
    if selected_patch and selected_patch != "all":
        scoped_entries = [
            entry
            for entry in set_entries
            if entry.get("patch") == selected_patch
        ]

    return {
        "entries": scoped_entries,
        "set_entries": set_entries,
        "available_sets": available_sets,
        "selected_set": selected_set,
        "selected_patch": selected_patch,
        "latest_set": latest_set,
        "latest_patch": latest_patch,
    }


def _parse_set_filter(value):
    if value in (None, "", "latest"):
        return None

    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Choose a valid TFT set.") from error


def _data_scope(entries, scope, all_entries):
    patches = _available_patches(all_entries, scope["selected_set"])

    return {
        "games": len(entries),
        "current_set": scope["selected_set"],
        "current_patch": scope["selected_patch"],
        "latest_set": scope["latest_set"],
        "latest_patch": scope["latest_patch"],
        "selected_set": scope["selected_set"],
        "selected_patch": scope["selected_patch"],
        "available_sets": scope["available_sets"],
        "patches": patches,
        "patch_count": len(patches),
    }


def _performance_score(entries):
    placements = [entry["placement"] for entry in entries if entry.get("placement")]
    games = len(placements)

    if not placements:
        return None

    avg_placement = sum(placements) / games
    recent_placements = placements[-20:]
    recent_avg = sum(recent_placements) / len(recent_placements)
    top4_rate = _top4_rate(placements)
    win_rate = (sum(1 for placement in placements if placement == 1) / games) * 100
    bottom4_rate = (sum(1 for placement in placements if placement >= 5) / games) * 100
    avg_score = _clamp((8 - avg_placement) / 7 * 100, 0, 100)
    recent_score = _clamp((8 - recent_avg) / 7 * 100, 0, 100)
    win_score = _clamp((win_rate / 18) * 100, 0, 100)
    consistency_score = _clamp(100 - bottom4_rate, 0, 100)
    confidence = min(games / 30, 1)
    raw_score = (
        avg_score * 0.35
        + top4_rate * 0.25
        + win_score * 0.15
        + recent_score * 0.15
        + consistency_score * 0.10
    )
    score = round(raw_score * (0.75 + confidence * 0.25))

    if score >= 90:
        label = "Elite"
        tone = "elite"
    elif score >= 80:
        label = "Great"
        tone = "great"
    elif score >= 70:
        label = "Strong"
        tone = "strong"
    elif score >= 60:
        label = "Steady"
        tone = "steady"
    elif score >= 45:
        label = "Developing"
        tone = "developing"
    else:
        label = "Review"
        tone = "review"

    return {
        "score": score,
        "label": label,
        "tone": tone,
        "games": games,
        "avg_placement": round(avg_placement, 2),
        "top4_rate": round(top4_rate, 2),
        "win_rate": round(win_rate, 2),
        "recent_avg_placement": round(recent_avg, 2),
        "confidence": round(confidence, 2),
    }


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _tag(label, tone, detail):
    return {
        "label": label,
        "tone": tone,
        "detail": detail,
    }


def _trait_breakpoint_rows(results, limit=16):
    rows = []

    for (name, num_units, style), placements in results.items():
        rows.append(
            {
                "name": name,
                "num_units": num_units,
                "tier_label": f"{num_units} {name}" if num_units else name,
                "style": style,
                "style_name": _trait_style_name(style),
                "games": len(placements),
                "avg_placement": round(sum(placements) / len(placements), 2),
                "top4_rate": round(_top4_rate(placements), 2),
            }
        )

    return sorted(rows, key=lambda row: (-row["games"], row["style"], row["avg_placement"]))[:limit]


def _trait_style_name(style):
    return {
        1: "bronze",
        2: "silver",
        3: "gold",
        4: "prismatic",
    }.get(style, "active")


def _performance_rows(results, name_key="name", limit=12):
    rows = []

    for name, placements in results.items():
        rows.append(
            {
                name_key: name,
                "games": len(placements),
                "avg_placement": round(sum(placements) / len(placements), 2),
                "top4_rate": round(_top4_rate(placements), 2),
            }
        )

    return sorted(rows, key=lambda row: (-row["games"], row["avg_placement"]))[:limit]


def _match_comp_units(comp_units, played_units):
    normalized_comp = {
        _normalize_name(unit): unit
        for unit in comp_units
        if unit
    }
    normalized_played = {
        _normalize_name(unit)
        for unit in played_units
        if unit
    }

    if not normalized_comp:
        return None

    matched_keys = set(normalized_comp) & normalized_played
    missing_keys = set(normalized_comp) - matched_keys
    allowed_missing = min(2, max(len(normalized_comp) - 1, 0))

    if len(missing_keys) > allowed_missing:
        return None

    return {
        "matched_units": [normalized_comp[key] for key in sorted(matched_keys)],
        "missing_units": [normalized_comp[key] for key in sorted(missing_keys)],
        "matched_count": len(matched_keys),
        "target_count": len(normalized_comp),
        "missing_count": len(missing_keys),
        "match_quality": _match_quality_label(len(missing_keys)),
    }


def _match_quality_label(missing_count):
    if missing_count == 0:
        return "Exact"

    return f"Missing {missing_count}"


def _academy_comp_row(comp, matches_for_comp, placements):
    games = len(placements)
    best_match = min(
        matches_for_comp,
        key=lambda match: (match.get("missing_count", 99), match.get("placement", 99)),
        default=None,
    )

    return {
        "slug": comp.get("slug"),
        "title": comp.get("title"),
        "tier": comp.get("tier") or "Unranked",
        "style": comp.get("style") or "",
        "units": comp.get("units", []),
        "games": games,
        "avg_placement": round(sum(placements) / games, 2) if games else None,
        "top4_rate": round(_top4_rate(placements), 2) if games else None,
        "win_rate": round((sum(1 for placement in placements if placement == 1) / games) * 100, 2) if games else None,
        "exact_games": sum(1 for match in matches_for_comp if match.get("missing_count") == 0),
        "near_games": sum(1 for match in matches_for_comp if match.get("missing_count") in (1, 2)),
        "best_match": best_match,
        "recent_matches": sorted(
            matches_for_comp,
            key=lambda match: match.get("game_datetime") or 0,
            reverse=True,
        )[:5],
    }


def _academy_comp_sort_key(row):
    tier_order = {
        "S": 0,
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "X": 5,
        "Unranked": 6,
    }

    return (
        0 if row["games"] else 1,
        tier_order.get(row["tier"], 7),
        -row["games"],
        row["avg_placement"] if row["avg_placement"] is not None else 99,
        row["title"] or "",
    )


def _augment_stats(results, saw_augment_data):
    return {
        "available": saw_augment_data,
        "source": "Riot match API",
        "message": (
            None
            if saw_augment_data
            else "Augments are not present in the Riot TFT match payload for these games."
        ),
        "performance": _performance_rows(results) if saw_augment_data else [],
    }


def _favorite_tactician(entries, sample_limit=50):
    recent_entries = entries[-sample_limit:]
    counter = Counter()
    last_seen = {}

    for index, entry in enumerate(recent_entries):
        tactician_id = entry.get("tactician")
        if not tactician_id:
            continue

        identity = (str(tactician_id), entry.get("tactician_content_id") or None)
        counter[identity] += 1
        last_seen[identity] = index

    if not counter:
        return None

    # Riot item_ID is the exact tactician/skin variant. If counts tie, the most
    # recently used identity is the best available signal for what is equipped.
    identity = max(counter, key=lambda key: (counter[key], last_seen[key]))
    tactician_id, content_id = identity
    games = counter[identity]
    details = _tactician_details(tactician_id)

    return {
        "id": tactician_id,
        "content_id": content_id,
        "name": details["name"],
        "image_url": details["image_url"],
        "games": games,
        "rate": round((games / len(recent_entries)) * 100, 2) if recent_entries else 0,
        "sample_size": len(recent_entries),
    }


def _available_sets(entries):
    sets = {
        entry.get("tft_set_number")
        for entry in entries
        if entry.get("tft_set_number") is not None
    }
    return sorted(sets, reverse=True)


def _available_patches(entries, set_number=None):
    patches = {
        entry["patch"]
        for entry in entries
        if entry.get("patch") and (set_number is None or entry.get("tft_set_number") == set_number)
    }
    return sorted(patches, reverse=True)


def _latest_value(entries, key):
    if not entries:
        return None

    latest_entry = max(entries, key=lambda entry: entry.get("game_datetime") or 0)
    return latest_entry.get(key)


def _current_tft_set():
    load_dotenv(override=True)
    return int(os.getenv("CURRENT_TFT_SET", "18"))


def _current_tft_patch():
    load_dotenv(override=True)
    return os.getenv("CURRENT_TFT_PATCH", "18.2")


def _tactician_details(tactician_id):
    fallback = {
        "name": f"Tactician {tactician_id}",
        "image_url": None,
    }

    try:
        catalog = _load_tactician_catalog()
    except requests.RequestException:
        return fallback

    tactician = catalog.get("data", {}).get(str(tactician_id))
    if not tactician:
        return fallback

    version = catalog.get("version")
    image = tactician.get("image", {}).get("full")

    return {
        "name": tactician.get("name") or fallback["name"],
        "image_url": (
            f"https://ddragon.leagueoflegends.com/cdn/{version}/img/tft-tactician/{image}"
            if version and image
            else None
        ),
    }


def _load_tactician_catalog():
    if TACTICIANS_CACHE_PATH.exists():
        with TACTICIANS_CACHE_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)

    versions = requests.get(DDRAGON_VERSIONS_URL, timeout=20)
    versions.raise_for_status()
    version = versions.json()[0]
    response = requests.get(
        f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/tft-tactician.json",
        timeout=20,
    )
    response.raise_for_status()
    catalog = response.json()
    catalog["version"] = version

    TACTICIANS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TACTICIANS_CACHE_PATH.open("w", encoding="utf-8") as file:
        json.dump(catalog, file)

    return catalog


def _parse_tftacademy_comps(html):
    comps = []
    seen = set()
    chunks = html.split("{altBuilds:")

    for chunk in chunks[1:]:
        chunk = "{altBuilds:" + chunk
        slug = _regex_value(chunk, r'compSlug:"([^"]+)"')
        title = _regex_value(chunk, r'title:"([^"]+)"')
        style = _regex_value(chunk, r'style:"([^"]*)"')
        tier = _regex_value(chunk, r'tier:"([^"]*)"') or "Unranked"

        if not slug or not title or slug in seen:
            continue

        final_comp = _extract_bracket_value(chunk, "finalComp:[")
        if not final_comp:
            continue

        units = [
            _clean_tft_name(unit_match.group(1))
            for unit_match in re.finditer(r'apiName:"([^"]+)"', final_comp)
        ]
        units = list(dict.fromkeys(units))

        if not units:
            continue

        if slug in seen:
            continue

        seen.add(slug)
        comps.append(
            {
                "slug": slug,
                "title": title,
                "tier": tier,
                "style": style,
                "units": units,
            }
        )

    return comps


def _regex_value(text, pattern):
    match = re.search(pattern, text, re.S)
    return match.group(1) if match else None


def _extract_bracket_value(text, marker):
    start = text.find(marker)
    if start == -1:
        return None

    index = start + len(marker)
    depth = 1
    in_string = False
    escaped = False

    while index < len(text):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return text[start + len(marker):index]

        index += 1

    return None
