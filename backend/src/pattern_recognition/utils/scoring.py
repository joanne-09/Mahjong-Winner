from .constants import (
    ALL_BONUS,
    BONUS_LABELS,
    DRAGON_LABELS,
    DRAGON_NAMES,
    DRAGON_ORDER,
    FLOWERS,
    SEASONS,
    SEAT_BONUS_TILES,
    SPECIAL_EVENT_DEFAULT_TAI,
    SUIT_LABELS,
    WIND_LABELS,
    words_index,
)
from .scoring_helpers import (
    analyze_breakdown,
    as_int,
    current_seat_wind,
    dealer_log_entry,
    dealer_tai,
    flag,
    is_self_draw,
    normalize_wind,
    tile_suit,
)


def calculate_tai(breakdown, bonus, others=None) -> tuple[int, list]:
    """
    Calculate all tai entries for a winning breakdown.
    Parameters:
        breakdown: list of tuple, the breakdown of the winning hand.
        bonus: list of int, the tiles of bonus.
        others: dict of table and event conditions, including round, seats, self draw, waits, etc.
    Returns:
        tai_count: int, the calculated tai count.
        tai_log: list, the log of tai calculated.
    """

    tai_log = []
    tai_count = 0
    others = others or {}
    bonus_tiles = set(bonus or [])

    if breakdown is None:
        return tai_count, tai_log

    analysis = analyze_breakdown(breakdown)
    all_tiles = analysis["all_tiles"]
    all_suits = [tile_suit(tile) for tile in all_tiles]
    number_suits = {suit for suit in all_suits if suit in SUIT_LABELS}
    pair_name = analysis["pair_name"]
    has_words = any(suit == "word" for suit in all_suits)
    all_words = bool(all_tiles) and all(suit == "word" for suit in all_suits)
    round_wind = normalize_wind(others.get("round"))
    seat_wind = current_seat_wind(others)
    self_draw = is_self_draw(others)
    see_flower_word = flag(
        others,
        "see_flower_word",
        "jian_hua_jian_zi",
        "star31_special",
        "count_every_flower_word",
    )


    def add(name: str, value: int):
        """Add one scoring item to the tai total and log."""
        nonlocal tai_count
        tai_count += value
        tai_log.append(f"{name} +{value}")


    def add_if_not_suppressed(pattern_key: str, name: str, value: int, suppressed: set):
        """Add one scoring item only when no higher rule suppresses it."""
        if pattern_key not in suppressed:
            add(name, value)

    def event_tai(key: str) -> int:
        """Return the configured tai value for a special event."""
        return as_int(others.get(f"{key}_tai"), SPECIAL_EVENT_DEFAULT_TAI[key])

    # Dealer/continuation tai are payer-specific, so calculate_money applies them separately.
    dealer_log = dealer_log_entry(others)
    if dealer_log:
        tai_log.append(dealer_log)

    suppressed = set()

    if flag(others, "heavenly_win", "tian_hu", "tenhou"):
        add("天胡", event_tai("heavenly_win"))
        suppressed.update(
            {
                "self_draw",
                "concealed",
                "no_call_self_draw",
                "single_wait",
                "kong_draw",
                "heavenly_ready",
                "earthly_ready",
            }
        )
    if flag(others, "human_win", "ren_hu", "renhou"):
        add("人胡", event_tai("human_win"))
        suppressed.update({"concealed", "heavenly_ready", "earthly_ready"})
    if flag(others, "earthly_win", "di_hu", "chiihou"):
        add("地胡", event_tai("earthly_win"))
        suppressed.update({"self_draw", "concealed", "no_call_self_draw", "heavenly_ready", "earthly_ready"})

    has_big_four_winds = set(words_index).issubset(analysis["wind_triplets"])
    has_small_four_winds = pair_name in words_index and len(analysis["wind_triplets"]) == 3
    if has_big_four_winds:
        add("大四喜", 16)
    if has_big_four_winds or has_small_four_winds:
        suppressed.update({"seat_wind", "round_wind"})

    has_heavenly_ready = flag(others, "heavenly_ready", "tian_ting", "tenpai_on_deal")
    has_earthly_ready = flag(others, "earthly_ready", "di_ting", "chi_ting")
    has_quan_qiu = flag(others, "quan_qiu", "all_melded_single_wait") and not self_draw
    if has_heavenly_ready or has_earthly_ready:
        suppressed.update({"concealed", "no_call_self_draw", "ready"})

    has_big_three_dragons = DRAGON_NAMES.issubset(analysis["dragon_triplets"])
    has_small_three_dragons = pair_name in DRAGON_NAMES and len(analysis["dragon_triplets"]) == 2
    has_all_bonus = ALL_BONUS.issubset(bonus_tiles)
    has_seven_robbing_one = flag(
        others,
        "seven_robbing_one",
        "seven_flowers_rob_one",
        "qi_qiang_yi",
        "qiang_hua",
        "seven_grab_one",
    )

    # 1 tai
    concealed = flag(others, "concealed", "is_concealed", "menqing", "men_qing", "closed_hand", "no_open_melds")
    if concealed and self_draw and not {"concealed", "self_draw"}.intersection(suppressed):
        add("門清自摸", 3)
    else:
        if concealed:
            add_if_not_suppressed("concealed", "門清", 1, suppressed)
        if self_draw:
            add_if_not_suppressed("self_draw", "自摸", 1, suppressed)

    if see_flower_word:
        for wind in words_index:
            if wind in analysis["wind_triplets"]:
                add(f"見風見台({WIND_LABELS[wind]})", 1)
        for tile in sorted(bonus_tiles):
            add(f"見花見台({BONUS_LABELS[tile]})", 1)
        if not has_words and not bonus_tiles:
            add("無字無花", 2)
    else:
        if seat_wind in analysis["wind_triplets"]:
            add_if_not_suppressed("seat_wind", f"風牌({WIND_LABELS[seat_wind]})", 1, suppressed)
        if round_wind in analysis["wind_triplets"]:
            add_if_not_suppressed("round_wind", f"風圈({WIND_LABELS[round_wind]})", 1, suppressed)

        if not has_all_bonus and not has_seven_robbing_one:
            for tile in sorted(bonus_tiles & SEAT_BONUS_TILES.get(seat_wind, set())):
                add(f"花牌({BONUS_LABELS[tile]})", 1)

    if not has_big_three_dragons and not has_small_three_dragons:
        for dragon in DRAGON_ORDER:
            if dragon not in analysis["dragon_triplets"]:
                continue
            add(f"三元牌({DRAGON_LABELS[dragon]})", 1)

    if flag(others, "rob_kong", "rob_gang", "qiang_gang", "chankan"):
        add("搶槓", event_tai("rob_kong"))

    exclusive_wait = flag(
        others,
        "single_wait",
        "du_ting",
        "exclusive_wait",
        "edge_wait",
        "closed_wait",
        "pair_wait",
    )
    if exclusive_wait and not has_quan_qiu:
        add_if_not_suppressed("single_wait", "獨聽", 1, suppressed)

    if flag(others, "kong_draw", "gang_shang_kai_hua", "after_kong", "rinshan"):
        add_if_not_suppressed("kong_draw", "槓上開花", event_tai("kong_draw"), suppressed)
    if flag(others, "last_discard", "river_last", "haitei_ron", "hedi"):
        add("河底撈魚", event_tai("last_discard"))
    if flag(others, "last_tile", "wall_last", "haitei", "haitei_tsumo"):
        add("海底撈月", event_tai("last_tile"))

    # 2 tai
    all_sequences = analysis["sequence_count"] == 5 and analysis["triplet_count"] == 0
    has_no_flowers = len(bonus_tiles) == 0
    pin_hu = (
        all_sequences
        and not has_words
        and has_no_flowers
        and not self_draw
        and not exclusive_wait
    )
    has_pin_hu = pin_hu or flag(others, "pin_hu", "ping_hu")
    if has_pin_hu:
        add("平胡", 2)

    if has_quan_qiu:
        add("全求", 2)

    if see_flower_word:
        open_kongs = (
            as_int(others.get("open_kongs"), 0)
            + as_int(others.get("melded_kongs"), 0)
            + as_int(others.get("added_kongs"), 0)
        )
        open_kongs = open_kongs or as_int(others.get("kongs"), 0)
        concealed_kongs = as_int(others.get("concealed_kongs"), 0)
        if open_kongs:
            add(f"槓牌 x{open_kongs}", open_kongs)
        if concealed_kongs:
            add(f"暗槓 x{concealed_kongs}", concealed_kongs * 2)

    if not has_all_bonus and not has_seven_robbing_one:
        if SEASONS.issubset(bonus_tiles):
            add("花槓(春夏秋冬)", 1)
        if FLOWERS.issubset(bonus_tiles):
            add("花槓(梅蘭菊竹)", 1)

    concealed_triplets = as_int(others.get("concealed_triplets"), 0)
    if concealed_triplets == 3 and not has_pin_hu:
        add("三暗刻", 2)

    # 4 tai
    if analysis["triplet_count"] == 5:
        add("碰碰胡", 4)

    if has_small_three_dragons:
        add("小三元", 4)

    if len(number_suits) == 1 and has_words:
        suit = next(iter(number_suits))
        add(f"混一色({SUIT_LABELS[suit]})", 4)

    # 5 tai
    if concealed_triplets == 4:
        add("四暗刻", 5)

    # 8 tai
    if has_earthly_ready:
        add_if_not_suppressed("earthly_ready", "地聽", event_tai("earthly_ready"), suppressed)

    if concealed_triplets == 5:
        add("五暗刻", 8)

    if has_big_three_dragons:
        add("大三元", 8)

    if has_small_four_winds:
        add("小四喜", 8)

    if len(number_suits) == 1 and not has_words:
        suit = next(iter(number_suits))
        add(f"清一色({SUIT_LABELS[suit]})", 8)

    if has_seven_robbing_one:
        add("七搶一", event_tai("seven_robbing_one"))

    if has_all_bonus:
        add("八仙過海", 8)

    # 16 tai
    if has_heavenly_ready:
        add_if_not_suppressed("heavenly_ready", "天聽", event_tai("heavenly_ready"), suppressed)

    if all_words:
        add("字一色", 16)

    return tai_count, tai_log


def calculate_money(tai_count: int, others: dict) -> dict:
    """
    Calculate payment deltas for all four seats.
    """
    money = {"east": 0, "south": 0, "west": 0, "north": 0}
    others = others or {}
    seat = normalize_wind(others.get("seat")) or others.get("seat")
    dealer = normalize_wind(others.get("dealer")) or others.get("dealer")
    wins = normalize_wind(others.get("wins")) or others.get("wins")
    base = as_int(others.get("base"), 0)
    bonus_money = as_int(others.get("bonus"), 0)
    dealer_money = dealer_tai(others)
    self_winning = is_self_draw(others)
    wins_from = seat if self_winning else wins
    normal_payment = base + bonus_money * tai_count
    dealer_payment = base + bonus_money * (tai_count + dealer_money)

    if seat not in money:
        raise ValueError(f"Invalid winning seat: {others.get('seat')}")
    if dealer not in money:
        raise ValueError(f"Invalid dealer seat: {others.get('dealer')}")
    if not self_winning and wins_from not in money:
        raise ValueError(f"Invalid discard source: {others.get('wins')}")

    # Calculate the money based on the tai count and winning conditions
    if self_winning and seat != dealer:
        money[seat] += normal_payment * 3 + bonus_money * dealer_money
        for other_seat in ["east", "south", "west", "north"]:
            if other_seat != seat:
                money[other_seat] -= normal_payment
        money[dealer] -= bonus_money * dealer_money
    elif self_winning and seat == dealer:
        money[seat] += dealer_payment * 3
        for other_seat in ["east", "south", "west", "north"]:
            if other_seat != seat:
                money[other_seat] -= dealer_payment
    elif wins_from == dealer or seat == dealer:
        money[seat] += dealer_payment
        money[wins_from] -= dealer_payment
    else:
        money[seat] += normal_payment
        money[wins_from] -= normal_payment

    return money
