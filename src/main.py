from pattern_recognition.tile_recognition import tile_recognition
from pattern_recognition.main import check_win_condition
from tile_generation.main import tile_generation

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

if __name__ == "__main__":    
    # Recognize the tiles
    image_path = "test.jpg"
    bing, bamboo, wan, words, bonus = tile_recognition(image_path)

    # Generate picture of tiles
    tiles = bing + bamboo + wan + words + bonus
    tile_generation(tiles)
    
    # Check the winning condition
    final_money, final_breakdown = check_win_condition(bing, bamboo, wan, words, bonus)
    print(f"Final money: {final_money}")
    print(f"Final breakdown: {final_breakdown}")