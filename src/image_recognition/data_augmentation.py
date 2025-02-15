import os
from glob import glob
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import cv2
import csv
import pickle
import random
import datetime
import time

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

# Specify the size of tiles
image_height = 1024
image_width = 1024

# Set the path to the background images
background_fn = "backgrounds.pck"
bg_path = "data/original/bg_img"
bg_images = []

# Set the path to the images and the output directory
image_path = "data/original/tiles-resized"  # Path to the images
output_path = "data/original/augmented"  # Path to the output directory
filenames = {}  # Get the list of filenames

# Create the output directory if it does not exist
os.makedirs(output_path, exist_ok=True)

# Load background images
print("Loading images...")
for subdir in glob(bg_path+"/*"):
    for f in glob(subdir+"/*.jpg"):
        bg_images.append(mpimg.imread(f))
pickle.dump(bg_images, open(background_fn, 'wb'))
print("Finish Loading background images")


class Backgrounds():
    def __init__(self, background_fn=background_fn):
        self.backgrounds = pickle.load(open(background_fn, 'rb'))
        self.bg_num = len(self.backgrounds)

    def get_random(self, display=False):
        bg = self.backgrounds[random.randint(0, self.bg_num-1)]
        if display:
            plt.imshow(bg)
            plt.show()
        return bg

# Initialize the background generator
backgrounds = Backgrounds()

# Load the labels of the images
labels = "data/original/tiles-data/data.csv"
tile_types = {}
with open(labels, newline='') as csvfile:
    table = csv.reader(csvfile, delimiter=' ')
    for row in table:
        row_data = row[0].split(",")
        filename = row_data[0]
        tile_label = row_data[1]

        if tile_label == 'label': 
            continue
        if ((tile_label in tile_types) is False):
            tile_types[tile_label] = 0
        if tile_label in filenames:
            filenames[tile_label].append(filename)
        else:
            filenames[tile_label] = [filename]

# Rotate the image to the given angle
def rotate_tile(image, angle):
    # Get the center of the image
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)

    # Get the rotation matrix
    matrix = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(matrix[0, 0])
    sin = np.abs(matrix[0, 1])

    # Compute new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))

    # Adjust the rotation matrix
    matrix[0, 2] += (nW / 2) - cX
    matrix[1, 2] += (nH / 2) - cY

    # Perform the actual rotation and return the image
    return cv2.warpAffine(image, matrix, (nW, nH))

# Resize the image
def resize_tile(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    # If both the width and height are None, return the original image
    if width is None and height is None:
        return image

    # Check if width is None
    if width is None:
        # Calculate the ratio of the height and construct the dimensions
        r = height / float(h)
        dim = (int(w * r), height)
    # Then height is None
    else:
        # Calculate the ratio of the width and construct the dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # Resize the image
    return cv2.resize(image, dim, interpolation=inter)

# Generate the augmented image information
def generate_images(grid_len=4):
    grid_sz = grid_len * grid_len

    tile_images = []
    tile_labels = []

    for grid_idx in range(grid_sz):
        tile_label = random.choice(list(filenames.keys()))
        tile_paths = filenames[tile_label]
        tile_image = cv2.cvtColor(cv2.imread(
            image_path + "/" + random.choices(tile_paths, k=1)[0])
            , cv2.COLOR_RGB2RGBA).copy()

        # Rotate the image
        modified_image = rotate_tile(tile_image, random.randint(0, 359))
        modified_image = resize_tile(modified_image, 
                                    height=int(image_height/(grid_len*1.5)),
                                    width=int(image_width/(grid_len*1.5)))
        tile_images.append(modified_image)
        tile_labels.append(tile_label)
    
    return (tile_images, tile_labels)

# Generate the augmented image
def generate_augmented_image(grid_len=4):
    # Generate the image information
    (tile_images, tile_labels) = generate_images(grid_len)

    # Randomly select the background image
    bg_image = backgrounds.get_random()

    # Copy the background image such that the image would not be modified
    output_image = cv2.cvtColor(bg_image, cv2.COLOR_RGB2RGBA).copy()
    output_image = cv2.resize(output_image, (image_width, image_height), interpolation=cv2.INTER_AREA)

    now = datetime.datetime.now()
    now_str = now.strftime("%Y%m%d-%H%M%S")
    output_filename = output_path + "/images/" + now_str + ".jpg"
    output_labels = output_path + "/labeled/" + now_str + ".txt"
    # create an empty txt file first
    with open(output_labels, "w") as file:
        pass

    # Place the grid on the resized background image
    for row_idx in range(grid_len):
        for col_idx in range(grid_len):
            index = row_idx * grid_len + col_idx
            tile_image = tile_images[index]
            tile_gray = cv2.cvtColor(tile_image, cv2.COLOR_BGR2GRAY)
            _, alpha = cv2.threshold(tile_gray, 0, 255, cv2.THRESH_BINARY)
            b, g, r, a = cv2.split(tile_image)
            tile_image = cv2.merge([b, g, r, alpha], 4)

            x_offset = int((col_idx / grid_len) * output_image.shape[1])
            y_offset = int((row_idx / grid_len) * output_image.shape[0])

            x1, x2 = x_offset, x_offset + tile_image.shape[1]
            y1, y2 = y_offset, y_offset + tile_image.shape[0]

            alpha_s = tile_image[:, :, 3] / 255.0
            alpha_l = 1.0 - alpha_s

            for c in range(0, 3):
                output_image[y1:y2, x1:x2, c] = (alpha_s * tile_image[:, :, c] + \
                                                 alpha_l * output_image[y1:y2, x1:x2, c])
        
            # Compute the value of relative coordinates
            min_x = x1 / output_image.shape[1]
            max_x = x2 / output_image.shape[1]
            min_y = y1 / output_image.shape[0]
            max_y = y2 / output_image.shape[0]

            # Write the label to the output file
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            img_width = max_x - min_x
            img_height = max_y - min_y
            with open(output_labels, "a") as file:
                file.write(f"{tile_labels[index]} {center_x} {center_y} {img_width} {img_height}\n")
        
    # Save the output image
    cv2.imwrite(output_filename, cv2.cvtColor(output_image, cv2.COLOR_RGBA2RGB))

# Main function
total_images = int(input("Enter the number of images to generate: "))
for idx in range(total_images):
    grid_len = random.randint(2, 8)

    print(f"Generating image {idx+1} with grid size {grid_len}x{grid_len}...")
    generate_augmented_image(grid_len)
    time.sleep(0.5)

print("Finish generating images")