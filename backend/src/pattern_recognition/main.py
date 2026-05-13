from copy import deepcopy
from collections import Counter
from ..tile_generation.main import tile_translation, tile_number
from .tile_recognition import tile_recognition
from .utils.constants import tile_numbers
from .utils.scoring import calculate_tai, calculate_money


# Core logic of backend
def check_win_condition(bing, bamboo, wan, words, bonus, others=None) -> tuple[dict, list, list]:
    """
    Check if the tiles can form a winning hand and the maximum money that can be won.
    """
    best_result = {
        "money": {"east": 0, "south": 0, "west": 0, "north": 0},
        "breakdown": [],
        "tai_log": []
    }
    
    shun = dui = ke = 0
    breakdown = []

    # Check the words first 28-34
    for x in range(28, 35):
        cnt = words.count(x)
        if cnt >= 3:
            ke += 1
            breakdown.append(("ke", x, x, x))
        elif cnt == 2:
            dui += 1
            breakdown.append(("dui", x, x))

    # Check shun and ke and eliminate dui first
    tile_count = Counter(bing + bamboo + wan)
    if dui == 0:
        # Try every possible dui
        print("PATTERN RECOGNITION: Try to form a dui first")
        for tile in tile_count:
            if tile_count[tile] >= 2:
                temp_count = deepcopy(tile_count)
                temp_count[tile] -= 2

                breakdown.append(("dui", tile, tile))
                check_sets(temp_count, breakdown, bonus, others, best_result, shun, ke)      
                breakdown.pop()
    else:
        print("PATTERN RECOGNITION: Already has a dui and form ke and shun instead")
        check_sets(tile_count, breakdown, bonus, others, best_result, shun, ke)

    return best_result["money"], best_result["breakdown"], best_result["tai_log"]


# Try to form every possible winning hand using recursion
def check_sets(tile_count, breakdown, bonus, others, best_result, shun=0, ke=0) -> None:
    """
    Try to form every possible winning hand using recursion.
    """
    # If no tiles left, return True
    if sum(tile_count.values()) == 0 and shun + ke == 5:
        tai_count, tmp_log = calculate_tai(breakdown, bonus, others)
        tmp_money = calculate_money(tai_count, others)

        if tmp_money[others["seat"]] > best_result["money"][others["seat"]]:
            best_result["money"] = tmp_money
            best_result["breakdown"] = deepcopy(breakdown)
            best_result["tai_log"] = deepcopy(tmp_log)

        print("PATTERN RECOGNITION: Form a winning hand...")
        return

    # If no tiles left but not enough sets, return False
    if shun + ke == 5 or sum(tile_count.values()) == 0:
        print("PATTERN RECOGNITION: Unable to form winning hand because of tile lacking")
        return

    # Find first available tile to form a shun or ke
    for tile in list(tile_count.keys()):
        if tile_count[tile] <= 0:
            continue

        # Try to form a ke
        if tile_count[tile] >= 3:
            temp_count = deepcopy(tile_count)
            temp_count[tile] -= 3

            if temp_count[tile] == 0:
                del temp_count[tile]

            breakdown.append(("ke", tile, tile, tile))
            check_sets(temp_count, breakdown, bonus, others, best_result, shun, ke + 1)      
            breakdown.pop() # Backtrack

        # Try to form a shun, words cannot form shun
        cur_tile = tile_translation(tile)
        tile_type = cur_tile[0] # bing, suo(bamboo), wan
        if tile_type in ["b", "s", "w"]:
            tile_n = tile_numbers.index(cur_tile[2:])

            # tile tile+1 tile+2
            if tile_n < 7:
                next1 = tile + 1
                next2 = tile + 2

                if next1 in tile_count and next2 in tile_count:
                    temp_count = deepcopy(tile_count)
                    temp_count[tile] -= 1
                    temp_count[next1] -= 1
                    temp_count[next2] -= 1

                    if temp_count[tile] == 0:
                        del temp_count[tile]
                    if temp_count[next1] == 0:
                        del temp_count[next1]
                    if temp_count[next2] == 0:
                        del temp_count[next2]

                    breakdown.append(("shun", tile, next1, next2))
                    check_sets(temp_count, breakdown, bonus, others, best_result, shun + 1, ke)
                    breakdown.pop() # Backtrack

    return
