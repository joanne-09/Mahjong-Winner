import os
import cv2

_this_dir = os.path.dirname(os.path.abspath(__file__))
index = ['blank',
        'b_one','b_two','b_three','b_four','b_five','b_six','b_seven','b_eight','b_nine',
        's_one','s_two','s_three','s_four','s_five','s_six','s_seven','s_eight','s_nine',
        'w_one','w_two','w_three','w_four','w_five','w_six','w_seven','w_eight','w_nine',
        'east','south','west','north','zong','fa','bai',
        'spring','summer','autumn','winter','plum','orchid','chrysanthemum','bamboo',]
tile_path = os.path.join(_this_dir, "assets/")
output_path = os.path.join(_this_dir, "../../static/outputs/output.png")

def tile_generation(tiles):
    # Load images based on the tile types
    images = []
    for tile in tiles:
        if tile > 0 and tile < 43:
            image = cv2.imread(tile_path + index[tile] + ".png", cv2.IMREAD_UNCHANGED)
            images.append(image)
        else:
            print("Invalid tile type: ", tile)
    
    # Concatenate images horizontally
    if images:
        final_image = cv2.hconcat(images)

        cv2.imwrite(output_path, final_image)
        print("Generated image saved as", output_path)
    else:
        print("No tiles to generate")


def tile_translation(tile):
    """
    Translate tile number to its name.
    """
    if tile > 0 and tile < 43:
        return index[tile]
    else:
        return "Invalid tile type"

def tile_number(tile):
    """
    Translate tile name to its number.
    """
    if tile in index:
        return index.index(tile)
    else:
        return 0  # Invalid tile name