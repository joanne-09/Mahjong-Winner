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
bg_path = "datasets/original/bg_img"
bg_images = []

# Set the path to the images and the output directory
image_path = "datasets/original/tiles-resized"  # Path to the images
output_path = "datasets/original/augmented"  # Path to the output directory
filenames = {}  # Get the list of filenames

# Create the output directory if it does not exist
os.makedirs(output_path, exist_ok=True)

# Load background images
if not os.path.exists(background_fn):
    print("Loading background images...")
    for subdir in glob(bg_path+"/*"):
        for f in glob(subdir+"/*.jpg"):
            bg_images.append(mpimg.imread(f))
    pickle.dump(bg_images, open(background_fn, 'wb'))
    print("Finish Loading background images")
else:
    print("Background images already loaded")


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
labels = "datasets/original/tiles-data/data.csv"
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
def generate_images(num_tiles=14):
    tile_images = []
    tile_labels = []

    for _ in range(num_tiles):
        tile_label = random.choice(list(filenames.keys()))
        tile_paths = filenames[tile_label]
        tile_image = cv2.cvtColor(cv2.imread(
            image_path + "/" + random.choices(tile_paths, k=1)[0])
            , cv2.COLOR_RGB2RGBA).copy()
        tile_images.append(tile_image)
        tile_labels.append(tile_label)
    
    return (tile_images, tile_labels)

# Generate the augmented image
def generate_augmented_image(num_tiles=14):
    # Generate the image information
    (tile_images, tile_labels) = generate_images(num_tiles)

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

    # Resize tiles so they fit nicely
    target_height = int(image_height / 3)
    resized_tiles = []
    tile_widths = []
    for tile_image in tile_images:
        r_tile = resize_tile(tile_image, height=target_height)
        resized_tiles.append(r_tile)
        tile_widths.append(r_tile.shape[1])
    
    total_width = sum(tile_widths)
    # Give some horizontal margin
    if total_width > image_width * 0.9:
        scale_down = (image_width * 0.9) / total_width
        target_height = int(target_height * scale_down)
        resized_tiles = []
        tile_widths = []
        for tile_image in tile_images:
            r_tile = resize_tile(tile_image, height=target_height)
            resized_tiles.append(r_tile)
            tile_widths.append(r_tile.shape[1])
        total_width = sum(tile_widths)

    row_img = np.zeros((target_height, total_width, 4), dtype=np.uint8)
    
    x_offset = 0
    tile_boxes = [] # (min_x, min_y, max_x, max_y) in row_img
    for i, r_tile in enumerate(resized_tiles):
        w = r_tile.shape[1]
        row_img[:, x_offset:x_offset+w] = r_tile
        tile_boxes.append((x_offset, 0, x_offset + w, target_height))
        x_offset += w

    angle = random.randint(0, 359)
    # Get the rotation matrix
    (h, w) = row_img.shape[:2]
    (cX, cY) = (w // 2, h // 2)

    matrix = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos_val = np.abs(matrix[0, 0])
    sin_val = np.abs(matrix[0, 1])

    nW = int((h * sin_val) + (w * cos_val))
    nH = int((h * cos_val) + (w * sin_val))

    matrix[0, 2] += (nW / 2) - cX
    matrix[1, 2] += (nH / 2) - cY

    rotated_row_img = cv2.warpAffine(row_img, matrix, (nW, nH))

    # Place rotated_row_img on background
    # Ensure it doesn't exceed background bounds; resize if needed
    if nW > image_width or nH > image_height:
        scale = min(image_width / nW, image_height / nH) * 0.9
        nW = int(nW * scale)
        nH = int(nH * scale)
        rotated_row_img = cv2.resize(rotated_row_img, (nW, nH), interpolation=cv2.INTER_AREA)
        matrix[0, :] *= scale
        matrix[1, :] *= scale

    start_x = (image_width - nW) // 2
    start_y = (image_height - nH) // 2
    
    # Overlay rotated row image on background
    y1, y2 = start_y, start_y + nH
    x1, x2 = start_x, start_x + nW
    
    alpha_s = rotated_row_img[:, :, 3] / 255.0
    alpha_l = 1.0 - alpha_s
    for c in range(0, 3):
        output_image[y1:y2, x1:x2, c] = (alpha_s * rotated_row_img[:, :, c] + \
                                         alpha_l * output_image[y1:y2, x1:x2, c])

    with open(output_labels, "a") as file:
        for i, (xmin, ymin, xmax, ymax) in enumerate(tile_boxes):
            # Calculate 4 corners of original tile box
            corners = np.array([
                [xmin, ymin, 1],
                [xmax, ymin, 1],
                [xmax, ymax, 1],
                [xmin, ymax, 1]
            ])
            # Apply affine transform
            rotated_corners = matrix.dot(corners.T).T
            
            # Translated to bounding box on output_image
            rotated_corners[:, 0] += start_x
            rotated_corners[:, 1] += start_y

            rx_min = np.min(rotated_corners[:, 0]) / output_image.shape[1]
            rx_max = np.max(rotated_corners[:, 0]) / output_image.shape[1]
            ry_min = np.min(rotated_corners[:, 1]) / output_image.shape[0]
            ry_max = np.max(rotated_corners[:, 1]) / output_image.shape[0]
            
            # Ensure within bounds
            rx_min = max(0, min(1, rx_min))
            rx_max = max(0, min(1, rx_max))
            ry_min = max(0, min(1, ry_min))
            ry_max = max(0, min(1, ry_max))

            center_x = (rx_min + rx_max) / 2
            center_y = (ry_min + ry_max) / 2
            width = rx_max - rx_min
            height = ry_max - ry_min
            
            file.write(f"{tile_labels[i]} {center_x} {center_y} {width} {height}\n")
        
    # Save the output image
    cv2.imwrite(output_filename, cv2.cvtColor(output_image, cv2.COLOR_RGBA2RGB))

# Main function
total_images = int(input("Enter the number of images to generate: "))
for idx in range(total_images):
    num_tiles_in_row = random.randint(5, 14)

    print(f"Generating image {idx+1} with {num_tiles_in_row} tiles in a row...")
    generate_augmented_image(num_tiles_in_row)
    time.sleep(0.5)

print("Finish generating images")