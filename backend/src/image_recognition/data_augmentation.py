import os
import argparse
from glob import glob
import numpy as np
import cv2
import csv
import pickle
import random
import datetime
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

# Specify the size of tiles
image_height = 1024
image_width = 1024

# Set the path to the background images
background_fn = os.path.join(THIS_FOLDER, "backgrounds.pck")
bg_path = os.path.join(THIS_FOLDER, "datasets", "original", "bg_img")
bg_images = []

# Set the path to the images and the output directory
image_path = os.path.join(THIS_FOLDER, "datasets", "original", "tiles-resized")  # Path to the images
output_path = os.path.join(THIS_FOLDER, "datasets", "original", "augmented")  # Path to the output directory
output_images_path = os.path.join(output_path, "images")
output_labels_path = os.path.join(output_path, "labeled")
filenames = {}  # Get the list of filenames
tile_cache = {}

# Create the output directory if it does not exist
os.makedirs(output_path, exist_ok=True)
os.makedirs(output_images_path, exist_ok=True)
os.makedirs(output_labels_path, exist_ok=True)

# Load background images
if not os.path.exists(background_fn):
    print("Loading background images...")
    for subdir in glob(bg_path+"/*"):
        for f in glob(subdir+"/*.jpg"):
            image = cv2.imread(f, cv2.IMREAD_COLOR)
            if image is not None:
                bg_images.append(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    with open(background_fn, "wb") as background_file:
        pickle.dump(bg_images, background_file)
    print("Finish Loading background images")
else:
    print("Background images already loaded")


class Backgrounds():
    def __init__(self, background_fn=background_fn):
        with open(background_fn, "rb") as background_file:
            raw_backgrounds = pickle.load(background_file)
        self.backgrounds = [
            cv2.resize(
                cv2.cvtColor(background, cv2.COLOR_RGB2RGBA),
                (image_width, image_height),
                interpolation=cv2.INTER_AREA,
            )
            for background in raw_backgrounds
        ]
        self.bg_num = len(self.backgrounds)

    def get_random(self, display=False):
        bg = random.choice(self.backgrounds)
        if display:
            import matplotlib.pyplot as plt
            plt.imshow(bg)
            plt.show()
        return bg

# Initialize the background generator
backgrounds = Backgrounds()

# Load the labels of the images
labels = os.path.join(THIS_FOLDER, "datasets", "original", "tiles-data", "data.csv")
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

# Store background image in cache
for tile_label, tile_paths in filenames.items():
    cached_images = []
    for tile_filename in tile_paths:
        tile_filepath = os.path.join(image_path, tile_filename)
        image = cv2.imread(tile_filepath, cv2.IMREAD_UNCHANGED)
        if image is None:
            continue
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGBA)
        elif image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
        cached_images.append(image)
    if cached_images:
        tile_cache[tile_label] = cached_images

tile_label_keys = list(tile_cache.keys())

if not tile_label_keys:
    raise RuntimeError("No tile images were loaded into cache. Check dataset paths and label CSV.")

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
        tile_label = random.choice(tile_label_keys)
        tile_image = random.choice(tile_cache[tile_label]).copy()
        tile_images.append(tile_image)
        tile_labels.append(tile_label)
    
    return (tile_images, tile_labels)

# Generate the augmented image
def _build_output_stem(task_index=None):
    now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    random_suffix = uuid.uuid4().hex[:8]
    pid = os.getpid()
    if task_index is None:
        return f"{now_str}-{pid}-{random_suffix}"
    return f"{now_str}-{pid}-{task_index}-{random_suffix}"


def generate_augmented_image(num_tiles=14, output_stem=None):
    # Generate the image information
    (tile_images, tile_labels) = generate_images(num_tiles)

    # Randomly select the background image
    bg_image = backgrounds.get_random()

    # Copy the background image such that the image would not be modified
    output_image = bg_image.copy()

    if output_stem is None:
        output_stem = _build_output_stem()
    output_filename = os.path.join(output_images_path, f"{output_stem}.jpg")
    output_labels = os.path.join(output_labels_path, f"{output_stem}.txt")

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
    
    alpha = (rotated_row_img[:, :, 3:4].astype(np.float32)) / 255.0
    foreground = rotated_row_img[:, :, :3].astype(np.float32)
    background = output_image[y1:y2, x1:x2, :3].astype(np.float32)
    blended = alpha * foreground + (1.0 - alpha) * background
    output_image[y1:y2, x1:x2, :3] = blended.astype(np.uint8)

    label_lines = []
    with open(output_labels, "w") as file:
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
            
            label_lines.append(f"{tile_labels[i]} {center_x} {center_y} {width} {height}\n")
        file.writelines(label_lines)
        
    # Save the output image
    cv2.imwrite(output_filename, cv2.cvtColor(output_image, cv2.COLOR_RGBA2BGR))


# Parallize image generateion
# python data_augmentation.py --total-images 20000 --workers 4
def _worker_generate_image(task_index, min_tiles, max_tiles, base_seed):
    seed = base_seed + task_index + (os.getpid() * 9973)
    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))

    num_tiles_in_row = random.randint(min_tiles, max_tiles)
    output_stem = _build_output_stem(task_index)
    generate_augmented_image(num_tiles_in_row, output_stem=output_stem)
    return (task_index, num_tiles_in_row)


def run_generation(total_images, workers=1, min_tiles=5, max_tiles=14):
    if workers <= 1:
        for idx in range(total_images):
            num_tiles_in_row = random.randint(min_tiles, max_tiles)
            print(f"Generating image {idx + 1} with {num_tiles_in_row} tiles in a row...")
            generate_augmented_image(num_tiles_in_row, output_stem=_build_output_stem(idx + 1))
        return

    base_seed = int(time.time() * 1000) & 0x7FFFFFFF
    print(f"Generating {total_images} images with {workers} workers...")
    completed = 0
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_worker_generate_image, idx + 1, min_tiles, max_tiles, base_seed)
            for idx in range(total_images)
        ]

        for future in as_completed(futures):
            _, num_tiles_in_row = future.result()
            completed += 1
            print(f"Generated image {completed}/{total_images} ({num_tiles_in_row} tiles)")


def benchmark_generation(total_images, workers, min_tiles, max_tiles):
    start_single = time.perf_counter()
    run_generation(total_images, workers=1, min_tiles=min_tiles, max_tiles=max_tiles)
    single_duration = time.perf_counter() - start_single

    start_multi = time.perf_counter()
    run_generation(total_images, workers=workers, min_tiles=min_tiles, max_tiles=max_tiles)
    multi_duration = time.perf_counter() - start_multi

    speedup = single_duration / multi_duration if multi_duration > 0 else 0
    print(f"Single worker time: {single_duration:.2f}s")
    print(f"{workers} workers time: {multi_duration:.2f}s")
    print(f"Speedup: {speedup:.2f}x")


def parse_args():
    parser = argparse.ArgumentParser(description="Mahjong tile augmentation generator")
    parser.add_argument("--total-images", type=int, default=None, help="Number of images to generate")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--min-tiles", type=int, default=5, help="Minimum tiles per generated image")
    parser.add_argument("--max-tiles", type=int, default=14, help="Maximum tiles per generated image")
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run sequential vs parallel benchmark using --total-images count",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    workers = max(1, args.workers)

    if args.total_images is None:
        total_images = int(input("Enter the number of images to generate: "))
    else:
        total_images = args.total_images

    min_tiles = min(args.min_tiles, args.max_tiles)
    max_tiles = max(args.min_tiles, args.max_tiles)

    if args.benchmark:
        benchmark_workers = workers if workers > 1 else max(2, (os.cpu_count() or 2) - 1)
        benchmark_generation(total_images, benchmark_workers, min_tiles, max_tiles)
    else:
        run_generation(total_images, workers=workers, min_tiles=min_tiles, max_tiles=max_tiles)

    print("Finish generating images")


if __name__ == "__main__":
    main()