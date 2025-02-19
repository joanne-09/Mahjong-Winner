from ultralytics import YOLO

# Load the model
model_path = "../image_recognition/runs/detect/weight/last.pt"
model = YOLO(model_path)

def tile_recognition(image_path):
    # Detect the tiles in the image
    results = model(image_path, conf=0.5)

    # Extract the bounding boxes and labels
    for result in results:
        bing = filter(lambda x: x.cls <= 9 and x.cls >= 1, result.boxes)
        bamboo = filter(lambda x: x.cls <= 18 and x.cls >= 10, result.boxes)
        wan = filter(lambda x: x.cls <= 27 and x.cls >= 19, result.boxes)
        words = filter(lambda x: x.cls <= 34 and x.cls >= 28, result.boxes)
        bonus = filter(lambda x: x.cls <= 42 and x.cls >= 35, result.boxes)
    
    return bing, bamboo, wan, words, bonus