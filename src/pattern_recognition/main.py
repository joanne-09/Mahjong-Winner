from tile_recognition import tile_recognition

# Load the image
image_path = "datasets/original/tiles-data/images/1.jpg"

# Detect the tiles in the image
bing, bamboo, wan, words, bonus = tile_recognition(image_path)