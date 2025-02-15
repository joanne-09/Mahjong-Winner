from ultralytics import YOLO

# Load the model
model = YOLO("yolo8n.pt")

# Train the model
train_results = model.train(
    data="data.yaml",
    epochs=100,
    batch=16,
)

# Evaluate the model
metrics = model.val()

# Save the model
model.save("best.pt")