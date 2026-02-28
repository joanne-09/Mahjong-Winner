import os
import pandas as pd

data_path = "datasets/original/tiles-resized"
output_path = "datasets/original/labeled"
labels = "datasets/original/tiles-data/data.csv"

label_data = pd.read_csv(labels)

for filename in os.listdir(data_path):
    if filename.endswith(".jpg"):
        print(f"Processing {filename}...")

        # get label for image
        label = label_data[label_data["image-name"] == filename]["label"].values[0]
        # replace jpg with txt
        output_name = os.path.join(output_path, filename.replace(".jpg", ".txt"))
        # create output file and write label
        with open(output_name, "w") as file:
            file.write(f"{label} 0.5 0.5 1 1\n")

print("Finish labeling data")