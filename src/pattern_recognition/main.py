from tile_recognition import tile_recognition

from collections import Counter

# Extract tile numbers and index
tile_numbers = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

# Load the image
image_path = "datasets/original/tiles-data/images/1.jpg"

# Detect the tiles in the image
bing, bamboo, wan, words, bonus = tile_recognition(image_path)

# Final result of the game
final_breakdown = None
final_money = 0

def check_win_condition(bing, bamboo, wan, words, bonus) -> tuple[int, list]:
    global final_breakdown, final_money
    shun = dui = ke = 0

    # Check the words first 28-34
    for x in range(28, 35):
        cnt = words.count(x)
        if cnt >= 3:
            ke += 1
        elif cnt == 2:
            dui += 1
    
    # Check shun and ke and eliminate dui first
    tile_count = Counter(bing + bamboo + wan)
    if dui == 0:
        # Try every possible dui
        for tile in tile_count:
            if tile_count[tile] >= 2:
                temp_count = tile_count.copy()
                temp_count[tile] -= 2

                breakdown = [("dui", tile, tile)]
                check_sets(temp_count, breakdown, bonus, shun, ke)
    
    return final_money, final_breakdown

# Check if the tiles can form sets using recursion
def check_sets(tile_count, breakdown, bonus, shun=0, ke=0) -> None:
    global final_breakdown, final_money

    # If no tiles left, return True
    if sum(tile_count.values()) == 0 and shun + ke == 5:
        tmp_money = check_winning_money(breakdown, bonus)
        if tmp_money > final_money:
            final_money = tmp_money
            final_breakdown = breakdown.copy()
        return
    
    # If no tiles left but not enough sets, return False
    if shun + ke == 5 or sum(tile_count.values()) == 0:
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
        ke += 1
        check_sets(temp_count, breakdown, shun, ke + 1)
        breakdown.pop() # Backtrack
        ke -= 1 # Backtrack
    
    # Try to form a shun
    tile_type = tile[0] # bing, suo(bamboo), wan
    if tile_type in ["b", "s", "w"]:
        tile_number = tile_numbers.index(tile[2:])

        # tile tile+1 tile+2
        if tile_number < 7:
            next1 = tile_type + "_" + tile_numbers[tile_number + 1]
            next2 = tile_type + "_" + tile_numbers[tile_number + 2]

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
                shun += 1
                check_sets(temp_count, breakdown, shun + 1, ke)
                breakdown.pop() # Backtrack
                shun -= 1 # Backtrack
    
    return

def check_winning_money(breakdown, bonus) -> int:
    # Check the winning money
    if breakdown is None:
        return 0

    # Check the breakdown
    for item in breakdown:
        if item[0] == "dui":
            return 2
        elif item[0] == "ke":
            return 4
        elif item[0] == "shun":
            return 8

    return 0