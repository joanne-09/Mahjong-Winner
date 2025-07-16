import os
from .pattern_recognition.tile_recognition import tile_recognition
from .pattern_recognition.main import check_win_condition, unpackage_breakdown_list
from .tile_generation.main import tile_generation

others = {
    "round": "east", # the current round
    "dealer": "east", # the seat of the dealer
    "continues": 1, # the number of continues of the dealer
    "dice": 18, # the number of the dice
    "seat": "east", # the seat of the winning player
    "wins": "east", # the seat of the player who fang chong

    "base": 100, # the base money for each wins
    "bonus": 30, # the bonus money for each tai
}
_this_dir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":    
    # Recognize the tiles
    image_path = os.path.join(_this_dir, "test.png")

    print("Recognizing tiles in", image_path)
    bing, bamboo, wan, words, bonus = tile_recognition(image_path)

    # Print the recognized tiles to check
    # print(f"Bing tiles: {bing}")
    # print(f"Bamboo tiles: {bamboo}")
    # print(f"Wan tiles: {wan}")
    # print(f"Word tiles: {words}")
    # print(f"Bonus tiles: {bonus}")

    # Generate picture of tiles
    print("Generating virtual tile image...")
    tiles = bing + bamboo + wan + words + bonus
    tile_generation(tiles)
    
    # Check the winning condition
    print("Checking win condition and money count...")
    final_money, final_breakdown = check_win_condition(bing, bamboo, wan, words, bonus)

    print(f"Final money: {final_money}")
    print(f"Final breakdown: {final_breakdown}")

    # Generate picture of the winning tiles
    print("Generating winning tiles image...")
    tiles = unpackage_breakdown_list(final_breakdown)
    tile_generation(tiles)