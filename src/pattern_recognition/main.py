from ..tile_generation.main import tile_translation, tile_number
from .tile_recognition import tile_recognition

from collections import Counter

# Extract tile numbers and index
tile_numbers = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
words_index = ['east', 'south', 'west', 'north']

# Final result of the game
final_money = {"east": 0, "south": 0, "west": 0, "north": 0}
final_breakdown = []

def check_win_condition(bing, bamboo, wan, words, bonus, others=None) -> tuple[dict, list]:
    """
    Check if the tiles can form a winning hand and the maximum money that can be won.
    Parameters:
        bing: list of int, the tiles of bing.
        bamboo: list of int, the tiles of bamboo.
        wan: list of int, the tiles of wan.
        words: list of int, the tiles of words.
        bonus: list of int, the tiles of bonus.
        others: list of conditions, including the current round, seats, etc.

    Returns:
        final_money: dict of int, the maximum money that can be won.
        final_breakdown: list of tuple, the breakdown of the winning hand.
    """

    global final_breakdown, final_money
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
                temp_count = tile_count.copy()
                temp_count[tile] -= 2

                breakdown.append(("dui", tile, tile))
                check_sets(temp_count, breakdown, bonus, others, shun, ke)
                breakdown.pop()
    else:
        print("PATTERN RECOGNITION: Already has a dui and form ke and shun instead")
        for tile in tile_count:
            check_sets(tile_count, breakdown, bonus, others, shun, ke)

    return final_money, final_breakdown


# Check if the tiles can form sets using recursion
def check_sets(tile_count, breakdown, bonus, others=None, shun=0, ke=0) -> None:
    """
    Try to form every possible winning hand using recursion.
    Parameters:
        tile_count: Counter, the count of each tile.
        breakdown: list of tuple, the breakdown of the current winning hand.
        bonus: list of int, the tiles of bonus.
        others: list of conditions, including the current round, seats, etc.
        shun: int, the number of shun.
        ke: int, the number of ke.
    Returns:
        None
    """

    global final_breakdown, final_money

    # If no tiles left, return True
    if sum(tile_count.values()) == 0 and shun + ke == 5:
        tmp_money = check_winning_money(breakdown, bonus, others)
        if tmp_money[others["seat"]] > final_money[others["seat"]]:
            final_money = tmp_money
            final_breakdown = breakdown.copy()
        
        print("PATTERN RECOGNITION: Form a winning hand...")
        return
    
    # If no tiles left but not enough sets, return False
    if shun + ke == 5 or sum(tile_count.values()) == 0:
        print("PATTERN RECOGNITION: Unable to form winning hand because of tile lacking")
        return

    # Find first available tile to form a shun or ke
    for tile in list(tile_count.keys()):
        if tile_count[tile] > 0:
            break
    
        # Try to form a ke
        if tile_count[tile] >= 3:
            temp_count = tile_count.copy()
            temp_count[tile] -= 3

            if temp_count[tile] == 0:
                del temp_count[tile]

            breakdown.append(("ke", tile, tile, tile))
            check_sets(temp_count, breakdown, bonus, others, shun, ke + 1)
            breakdown.pop() # Backtrack
    
        # Try to form a shun, words cannot form shun
        cur_tile = tile_translation(tile)
        tile_type = cur_tile[0] # bing, suo(bamboo), wan
        if tile_type in ["b", "s", "w"]:
            tile_number = tile_numbers.index(cur_tile[2:])

            # tile tile+1 tile+2
            if tile_number < 7:
                next1 = tile + 1
                next2 = tile + 2

                if next1 in tile_count and next2 in tile_count:
                    temp_count = tile_count.copy()
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
                    check_sets(temp_count, breakdown, bonus, others, shun + 1, ke)
                    breakdown.pop() # Backtrack
    
    return


# Check the winning money
def check_winning_money(breakdown, bonus, others=None) -> dict:
    """
    Check the winning money based on the breakdown.
    Parameters:
        breakdown: list of tuple, the breakdown of the winning hand.
        bonus: list of int, the tiles of bonus.
        others: list of conditions, including the current round, seats, etc.
    Returns:
        money: dict, the winning money.
    """

    money = {"east": 0, "south": 0, "west": 0, "north": 0}

    self_winning = False
    dealer_winning = 0

    # Check the winning money
    if breakdown is None:
        return money
    
    # Check if someone fang chong, if self_winning then all other 3 players lose
    if others["seat"] == others["wins"]:
        self_winning = True
    
    # Check if the winning player is the host
    if others is not None and others["dealer"] == others["seat"]:
       dealer_winning = 2 * others["continues"] - 1
    # Check if the host is the fong chong player or self_winning
    elif others is not None and (others["wins"] == others["dealer"] or self_winning):
        dealer_winning = -1 * (2 * others["continues"] - 1)

    # Check the breakdown
    tai_count = 0

    """
    player has words of current round: 1
    player has words of the seat: 1
    player has bonus spring, summer, autumn, winter: 1
    player has bonus plum, orchid, chrysanthemum, bamboo: 1
    player has all ke: 4
    player has all with same type with words: 4
    player has all with same type without words: 8
    player has only words: 8
    player has zong, fa, bai, but one is dui: 4
    player has zong, fa, bai, but all are ke: 8
    player has east, south, west, north, but one is dui: 8
    player has east, south, west, north, but all are ke: 16
    """

    other_types = {"word": [], "bamboo": 0, "wan": 0, "bing": 0}
    dui_type = ""
    shun_count = ke_count = 0

    # Check the type of each set in the breakdown
    for item in breakdown:
        if item[0] == "dui":
            tile_name = tile_translation(item[1])
            if item[1] >= 28 and item[1] <= 34:
                dui_type = tile_name
            elif tile_name[0] == "b":
                dui_type = "bing"
            elif tile_name[0] == "w":
                dui_type = "wan"
            elif tile_name[0] == "s":
                dui_type = "bamboo"

        else:
            if item[0] == "shun":
                shun_count += 1
            elif item[0] == "ke":
                ke_count += 1

            tile_name = tile_translation(item[1])
            if item[1] >= 28 and item[1] <= 34:
                other_types["word"].append(tile_name)
            elif tile_name[0] == "b":
                other_types["bing"] += 1
            elif tile_name[0] == "w":
                other_types["wan"] += 1
            elif tile_name[0] == "s":
                other_types["bamboo"] += 1

    # Check if the player has words of the current round
    if others["round"] in other_types["word"]:
        tai_count += 1
    # Check if the player has words of the seat
    current_seat = (words_index[others["seat"]] - words_index[others["dealer"]] + 4) % 4
    if words_index[current_seat] in other_types["word"]:
        tai_count += 1
    # Check if the player has bonus spring, summer, autumn, winter
    if bonus is not None and any(tile in bonus for tile in range(35, 39)):
        tai_count += 1
    # Check if the player has bonus plum, orchid, chrysanthemum, bamboo
    if bonus is not None and any(tile in bonus for tile in range(39, 43)):
        tai_count += 1
    # Check if the player has all ke
    if ke_count == 5:
        tai_count += 4
    # Check if the player has all with same type
    if dui_type == "bing":
        if other_types["bamboo"] == 0 and other_types["wan"] == 0 and len(other_types["word"]) == 0:
            tai_count += 8
        elif other_types["bamboo"] == 0 and other_types["wan"] == 0:
            tai_count += 4
    elif dui_type == "wan":
        if other_types["bamboo"] == 0 and other_types["bing"] == 0 and len(other_types["word"]) == 0:
            tai_count += 4
        elif other_types["bamboo"] == 0 and other_types["bing"] == 0:
            tai_count += 8
    elif dui_type == "bamboo":
        if other_types["bing"] == 0 and other_types["wan"] == 0 and len(other_types["word"]) == 0:
            tai_count += 8
        elif other_types["bing"] == 0 and other_types["wan"] == 0:
            tai_count += 4
    else:
        if len(other_types["word"]) == 5:
            tai_count += 8
        elif len(other_types["word"]) + other_types["bamboo"] == 5 or \
             len(other_types["word"]) + other_types["wan"] == 5 or \
             len(other_types["word"]) + other_types["bing"] == 5:
            tai_count += 4
    # Check if the player has zong, fa, bai
    if dui_type not in ["zong", "fa", "bai"]:
        if all(tile in other_types["word"] for tile in ["zong", "fa", "bai"]):
            tai_count += 8
    elif dui_type == "zong" and all(tile in other_types["word"] for tile in ["fa", "bai"]):
        tai_count += 4
    elif dui_type == "fa" and all(tile in other_types["word"] for tile in ["zong", "bai"]):
        tai_count += 4
    elif dui_type == "bai" and all(tile in other_types["word"] for tile in ["zong", "fa"]):
        tai_count += 4
    # Check if the player has east, south, west, north
    if dui_type not in words_index:
        if all(tile in other_types["word"] for tile in words_index):
            tai_count += 16
    elif dui_type == "east" and all(tile in other_types["word"] for tile in ["south", "west", "north"]):
        tai_count += 8
    elif dui_type == "south" and all(tile in other_types["word"] for tile in ["east", "west", "north"]):
        tai_count += 8
    elif dui_type == "west" and all(tile in other_types["word"] for tile in ["east", "south", "north"]):
        tai_count += 8
    elif dui_type == "north" and all(tile in other_types["word"] for tile in ["east", "south", "west"]):
        tai_count += 8
    
    # Calculate the money based on the tai count and winning conditions
    if self_winning:
        for seat in words_index:
            if seat == others["seat"]:
                money[seat] += (others["base"] + others["bonus"] * (tai_count + others["continues"])) * 3
            else:
                money[seat] -= (others["base"] + others["bonus"] * (tai_count + others["continues"]))
    elif others["wins"] == others["dealer"]:
        money[others["seat"]] += (others["base"] + others["bonus"] * (tai_count + others["continues"]))
        money[others["wins"]] -= (others["base"] + others["bonus"] * (tai_count + others["continues"]))
    else:
        money[others["seat"]] += (others["base"] + others["bonus"] * tai_count)
        money[others["wins"]] -= (others["base"] + others["bonus"] * tai_count)

    return money


# Unpackage the breakdown list to a more usable format
def unpackage_breakdown_list(breakdown: list) -> list:
    """
    Unpackage the breakdown list to a more readable format.
    Parameters:
        breakdown: list of tuple, the breakdown of the winning hand.
    Returns:
        unpackaged_breakdown: list of int, the unpackaged breakdown.
    """
    unpackaged_breakdown = []
    for item in breakdown:
        if item[0] == "dui":
            unpackaged_breakdown.extend([item[1], item[2]])
        else:
            unpackaged_breakdown.extend([item[1], item[2], item[3]])
    
    return unpackaged_breakdown