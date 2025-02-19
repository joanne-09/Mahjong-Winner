from ultralytics import YOLO

# Load the model
model_path = "runs/detect/train3/last.pt"
model = YOLO(model_path)

# Train the model
train_results = model.train(
    data="data.yaml",
    epochs=5,
    batch=16,
    imgsz=1024,
    device="cpu",
)

# Evaluate the model
metrics = model.val()