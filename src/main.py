from pattern_recognition.tile_recognition import tile_recognition
from pattern_recognition.main import check_win_condition
from tile_generation.main import generate_tiles

if __name__ == "__main__":
    # Generate the tiles
    generate_tiles()
    
    # Recognize the tiles
    image_path = "test.jpg"
    bing, bamboo, wan, words, bonus = tile_recognition(image_path)
    
    # Check the winning condition
    final_money, final_breakdown = check_win_condition(bing, bamboo, wan, words, bonus)
    print(f"Final money: {final_money}")
    print(f"Final breakdown: {final_breakdown}")