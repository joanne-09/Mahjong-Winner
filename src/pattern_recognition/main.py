from tile_recognition import tile_recognition

from collections import Counter

# Load the image
image_path = "datasets/original/tiles-data/images/1.jpg"

# Detect the tiles in the image
bing, bamboo, wan, words, bonus = tile_recognition(image_path)

def check_win_condition(bing, bamboo, wan, words):
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

def check_sets(tile_count, shun=0, ke=0):
    # If no tiles left, return True
    if sum(tile_count.values()) == 0 and shun + ke == 5:
        return True