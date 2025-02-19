from ultralytics import YOLO
import yaml

# Load the config
config_path = "configs/train3.yaml"
with open(config_path, "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# Load the model
model = YOLO(config["model"])

# Train the model
train_results = model.train(**config)
