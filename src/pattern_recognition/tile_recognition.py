from ultralytics import YOLO

# Load the model
model_path = "../image_recognition/runs/detect/weight/last.pt"
model = YOLO(model_path)

def tile_recognition(image_path):
    # Detect the tiles in the image
    results = model(image_path, conf=0.5)

    # Initialize the lists
    bing = bamboo = wan = words = bonus = []

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