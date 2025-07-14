from ultralytics import YOLO
import os

# Load the model
_this_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(_this_dir, "..", "image_recognition", "runs", "detect", "train3", "weights", "last.pt")
model = YOLO(model_path)

def tile_recognition(image_path):
    # Detect the tiles in the image
    results = model(image_path, conf=0.5)

    # Initialize the lists
    bing = []     # 1-9
    bamboo = []  # 10-18
    wan = []     # 19-27
    words = []   # 28-34
    bonus = []   # 35-42

    # Extract the bounding boxes and labels
    for result in results:
        for box in result.boxes:
            cls = int(box.cls)

            if cls <= 9 and cls >= 1:
                bing.append(cls)
            elif cls <= 18 and cls >= 10:
                bamboo.append(cls)
            elif cls <= 27 and cls >= 19:
                wan.append(cls)
            elif cls <= 34 and cls >= 28:
                words.append(cls)
            elif cls <= 42 and cls >= 35:
                bonus.append(cls)
    
    return bing, bamboo, wan, words, bonus