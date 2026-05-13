from .constants import DRAGON_NAMES, TILE_NAMES, TRIPLET_TYPES, TRUE_VALUES, WIND_ALIASES, SELF_DRAW_ALIASES, words_index


def as_bool(value) -> bool:
    """Convert common form values into a boolean."""
    if isinstance(value, str):
        return value.strip().lower() in TRUE_VALUES
    return bool(value)


def flag(others: dict, *names: str) -> bool:
    """Return whether any named option in others is truthy."""
    return any(as_bool(others.get(name)) for name in names)


def as_int(value, default=0) -> int:
    """Convert a value to int and fall back when conversion fails."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_wind(value):
    """Normalize wind aliases into the internal east/south/west/north names."""
    if value is None:
        return None

    return WIND_ALIASES.get(str(value).strip().lower())


def current_seat_wind(others: dict):
    """Calculate the winner's relative seat wind from winner and dealer."""
    seat = normalize_wind(others.get("seat"))
    dealer = normalize_wind(others.get("dealer")) or "east"
    if seat not in words_index or dealer not in words_index:
        return seat

    seat_index = (words_index.index(seat) - words_index.index(dealer)) % len(words_index)
    return words_index[seat_index]


def is_self_draw(others: dict) -> bool:
    """Return whether the win should be treated as self-drawn."""
    wins_from = str(others.get("wins", "")).strip().lower()
    seat = str(others.get("seat", "")).strip().lower()
    return (
        wins_from in SELF_DRAW_ALIASES
        or (seat != "" and wins_from == seat)
        or flag(others, "self_draw", "tsumo", "zimo")
    )


def dealer_tai(others: dict) -> int:
    """Calculate dealer and continuation tai for payment purposes."""
    continues = max(as_int(others.get("continues"), 0), 0)
    return 2 * continues + 1


def dealer_log_entry(others: dict):
    """Build a display-only log line for dealer and continuation tai."""
    if "dealer" not in others or "seat" not in others:
        return None

    tai = dealer_tai(others)
    if tai <= 0:
        return None

    dealer = normalize_wind(others.get("dealer"))
    seat = normalize_wind(others.get("seat"))
    wins_from = normalize_wind(others.get("wins"))

    if seat == dealer:
        label = "莊家" if tai == 1 else "莊家/連莊/拉莊"
        return f"{label} +{tai}"
    if wins_from == dealer:
        label = "莊家放槍" if tai == 1 else "莊家連莊放槍"
        return f"{label} +{tai}"

    return None


def tile_suit(tile: int):
    """Return the internal suit category for a tile id."""
    if 1 <= tile <= 9:
        return "bing"
    if 10 <= tile <= 18:
        return "bamboo"
    if 19 <= tile <= 27:
        return "wan"
    if 28 <= tile <= 34:
        return "word"
    return None


def tile_name(tile: int) -> str:
    """Return the data.yaml-style tile name for a tile id."""
    if 0 <= tile < len(TILE_NAMES):
        return TILE_NAMES[tile]
    return "Invalid tile type"


def is_triplet(item) -> bool:
    """Return whether a breakdown item is a triplet or kong."""
    kind = item[0]
    tiles = item[1:]
    return kind in TRIPLET_TYPES or (len(tiles) >= 3 and len(set(tiles)) == 1)


def analyze_breakdown(breakdown):
    """Summarize a winning breakdown into counts and honor groups."""
    analysis = {
        "all_tiles": [],
        "pair_tile": None,
        "pair_name": None,
        "sequence_count": 0,
        "triplet_count": 0,
        "triplet_tiles": [],
        "triplet_names": [],
        "wind_triplets": set(),
        "dragon_triplets": set(),
    }

    for item in breakdown:
        if not item:
            continue

        kind = item[0]
        tiles = list(item[1:])
        analysis["all_tiles"].extend(tiles)

        if kind == "dui" and tiles:
            analysis["pair_tile"] = tiles[0]
            if tile_suit(tiles[0]) == "word":
                analysis["pair_name"] = tile_name(tiles[0])
        elif kind == "shun":
            analysis["sequence_count"] += 1
        elif is_triplet(item) and tiles:
            tile = tiles[0]
            name = tile_name(tile)
            analysis["triplet_count"] += 1
            analysis["triplet_tiles"].append(tile)

            if tile_suit(tile) == "word":
                analysis["triplet_names"].append(name)
                if name in words_index:
                    analysis["wind_triplets"].add(name)
                elif name in DRAGON_NAMES:
                    analysis["dragon_triplets"].add(name)

    return analysis
