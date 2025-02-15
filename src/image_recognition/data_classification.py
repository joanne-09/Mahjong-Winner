import os
import shutil
import random

original_data = "data/original/augmented/"
image_data = "data/images/"
label_data = "data/labels/"

# All the image files
image_files = os.listdir(os.path.join(original_data, "images"))

# Shuffle the image files
random.shuffle(image_files)

# Set split ratio
split_ratio = 0.8
split_index = int(len(image_files) * split_ratio)

train_images = image_files[:split_index]
val_images = image_files[split_index:]

def move_files(files, direction):
    for file in files:
        file_name = os.path.split(file)[-1]
        image_src = os.path.join(original_data, "images", file_name)
        label_src = os.path.join(original_data, "labeled", file_name.replace(".jpg", ".txt"))
        image_dest = os.path.join(image_data, direction, file_name)
        label_dest = os.path.join(label_data, direction, file_name.replace(".jpg", ".txt"))
        
        shutil.move(image_src, image_dest)
        shutil.move(label_src, label_dest)

move_files(train_images, "train")
move_files(val_images, "val")