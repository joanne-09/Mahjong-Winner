import os

if __package__ in (None, ""):
    import sys

    _this_file_dir = os.path.dirname(os.path.abspath(__file__))
    _backend_dir = os.path.dirname(_this_file_dir)
    if _backend_dir not in sys.path:
        sys.path.insert(0, _backend_dir)

    from src.pattern_recognition.tile_recognition import tile_recognition
    from src.pattern_recognition.main import check_win_condition
    from src.pattern_recognition.utils.formatting import unpackage_breakdown_list
    from src.tile_generation.main import tile_generation
else:
    from .pattern_recognition.tile_recognition import tile_recognition
    from .pattern_recognition.main import check_win_condition
    from .pattern_recognition.utils.formatting import unpackage_breakdown_list  
    from .tile_generation.main import tile_generation

others = {
    "round": "east", # the current round
    "dealer": "east", # the seat of the dealer
    "continues": 0, # the number of dealer continuations
    "dice": 18, # the number of the dice
    "seat": "east", # the seat of the winning player
    "wins": "east", # the seat of the player who fang chong

    "base": 100, # the base money for each wins
    "bonus": 30, # the bonus money for each tai

    "concealed": False, # whether the hand is closed
    "ready": False, # whether the winner declared ready
    "heavenly_win": False, # whether the hand is tian hu
    "heavenly_win_tai": 24, # tai value for tian hu
    "human_win": False, # whether the hand is ren hu
    "human_win_tai": 16, # tai value for ren hu
    "earthly_win": False, # whether the hand is di hu
    "earthly_win_tai": 16, # tai value for di hu
    "heavenly_ready": False, # whether the hand is tian ting
    "heavenly_ready_tai": 16, # tai value for tian ting
    "earthly_ready": False, # whether the hand is di ting
    "earthly_ready_tai": 8, # tai value for di ting
    "seven_robbing_one": False, # whether the hand is qi qiang yi
    "seven_robbing_one_tai": 8, # tai value for qi qiang yi
    "rob_kong": False, # whether the win is by robbing a kong
    "rob_kong_tai": 1, # tai value for robbing a kong
    "single_wait": False, # whether the win is on a single wait
    "half_qiu": False, # whether the hand qualifies for half-qiu
    "kong_draw": False, # whether the win is after a kong draw
    "kong_draw_tai": 1, # tai value for kong draw
    "last_discard": False, # whether the win is on the last discard
    "last_discard_tai": 1, # tai value for last discard
    "last_tile": False, # whether the win is on the last wall tile
    "last_tile_tai": 1, # tai value for last wall tile
    "quan_qiu": False, # whether the hand qualifies for quan-qiu
    "see_flower_word": False, # whether to use the GameTower flower/word rule
    "open_kongs": 0, # number of open or added kongs
    "concealed_kongs": 0, # number of concealed kongs
    "concealed_triplets": 0, # number of concealed triplets
}
_this_dir = os.path.dirname(os.path.abspath(__file__))

def resolve_output_path(output_filename):
    if not output_filename:
        return None
    if os.path.isabs(output_filename):
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        return output_filename

    output_dir = os.path.abspath(
        os.getenv("OUTPUT_FOLDER", os.path.join(_this_dir, "..", "var", "media", "outputs"))
    )
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, output_filename)

def backend_main(others_settings=None, output_filename=None):
    if others_settings is None:
        others_settings = others

    bing = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    bamboo = [10, 11, 12, 10, 11, 12, 10, 11]
    wan = []
    words = []
    bonus = []

    # Recognize the tiles
    final_money, final_breakdown, final_tai_log = check_win_condition(bing, bamboo, wan, words, bonus, others_settings)

    # Generate picture of the winning tiles
    print("Generating winning tiles image...")
    print("final_breakdown: ", final_breakdown)
    tiles = unpackage_breakdown_list(final_breakdown)
    
    # Determine save path if filename is provided
    save_path = resolve_output_path(output_filename)
        
    tile_generation(tiles, output=True, save_path=save_path)

    return final_money, final_breakdown, final_tai_log


# Core logic of backend
def final_backend_main(file_path: str, others_settings=None, output_filename=None): 
    if others_settings is None:
        others_settings = others

    # Recognize the tiles
    print("Recognizing tiles in", file_path)
    bing, bamboo, wan, words, bonus = tile_recognition(file_path)

    # Print the recognized tiles to check
    print(f"Bing tiles: {bing}")
    print(f"Bamboo tiles: {bamboo}")
    print(f"Wan tiles: {wan}")
    print(f"Word tiles: {words}")
    print(f"Bonus tiles: {bonus}")

    # Generate picture of tiles
    print("Generating virtual tile image...")
    tiles = bing + bamboo + wan + words + bonus
    tile_generation(tiles, output=False)
    
    # Check the winning condition
    print("Checking win condition and money count...")
    final_money, final_breakdown, final_tai_log = check_win_condition(bing, bamboo, wan, words, bonus, others_settings)

    print(f"Final money: {final_money}")
    print(f"Final breakdown: {final_breakdown}")
    print(f"Final tai log: {final_tai_log}")

    # Generate picture of the winning tiles
    print("Generating winning tiles image...")
    tiles = unpackage_breakdown_list(final_breakdown)
    
    save_path = resolve_output_path(output_filename)
        
    tile_generation(tiles, output=True, save_path=save_path)

    return final_money, final_breakdown, final_tai_log

if __name__ == "__main__":
    final_money, final_breakdown, final_tai_log = final_backend_main("test2.jpg")
