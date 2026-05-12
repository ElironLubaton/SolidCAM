import os
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw


# ==========================================
# Task 1: Load a PNG image and show it
# ==========================================
def load_and_show_image(image_path):
    """
    Loads an image from the given path and displays it.
    """
    # Load the image using Pillow
    img = Image.open(image_path)

    # Display the image using Matplotlib
    # plt.figure(figsize=(8, 8)) # Adjust size as needed
    plt.imshow(img)
    plt.axis('off')  # Hides the axes for a cleaner look
    plt.title("Original Image")
    plt.show()

    return img


# ==========================================
# Task 2: Draw a red rectangle from 4 coordinates
# ==========================================
def draw_red_rectangle(image, corners_set):
    """
    Takes a PIL Image object and a list of 4 (x, y) coordinates,
    draws a red outline connecting them, and displays the result.
    """
    # Create a copy so we don't modify the original image directly
    img_with_rect = image.copy()

    # Initialize the drawing context
    draw = ImageDraw.Draw(img_with_rect)

    # Draw a polygon using the 4 coordinates
    # outline="red" sets the color, width=3 sets the thickness
    for corners in corners_set:
        draw.polygon(corners, outline="red", width=3)

    # Display the updated image
    # plt.figure(figsize=(8, 8))
    plt.imshow(img_with_rect)
    plt.axis('off')
    plt.title("Image with Red Rectangle")
    plt.show()

    return img_with_rect


def scale_back(img_width, img_height, corners_set):
    """ Scale coordinates from 0-1000 back to actual image pixels """

    scaled_corners_set = []
    for box in corners_set:
        scaled_box = [
            (int((x / 1000.0) * img_width), int((y / 1000.0) * img_height))
            for x, y in box
        ]
        scaled_corners_set.append(scaled_box)

    return scaled_corners_set


def crop_and_save_areas(image_path, corners_set, output_folder="extracted_features"):
    """
    Crops specific areas from an image and saves them as lossless PNGs.
    """
    # 1. Create output directory if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created folder: {output_folder}")

    # 2. Open the source image
    img = Image.open(image_path)
    print(f"Processing source image: {image_path} ({img.size[0]}x{img.size[1]})")

    for index, corners in enumerate(corners_set):
        # 3. Calculate bounding box (left, top, right, bottom)
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        bbox = (min(xs), min(ys), max(xs), max(ys))

        # 4. Perform the crop (Pillow's crop is a 'lazy' operation, no data lost here)
        cropped_img = img.crop(bbox)

        # 5. Save as lossless PNG
        # Sanitize filename: replace spaces with underscores
        filename = f"{index}.png"
        save_path = os.path.join(output_folder, filename)

        # Using optimize=False ensures the fastest save without affecting pixel data.
        # PNG format is inherently lossless.
        plt.imshow(cropped_img)
        plt.axis('off')
        plt.show()
        cropped_img.save(save_path, format='PNG')
        print(f"Saved: {save_path} | Size: {cropped_img.size[0]}x{cropped_img.size[1]}\n\n")


##################################

image_path = "/content/TestExtended_Page_3.png"

# 1. Load and show
my_image = load_and_show_image(image_path)
print("\n")

# 2. Define 4 corners: [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
corners_set = [
    [(310, 40), (480, 40), (480, 130), (310, 130)],  # Top Center-Left Callout
    [(340, 365), (495, 365), (495, 455), (340, 455)],  # Center Callout
    [(265, 475), (415, 475), (415, 585), (265, 585)],  # Center Bottom-Left Callout + GD&T
    [(750, 240), (975, 240), (975, 290), (750, 290)],  # Top-Right Callout (2X)
    [(830, 290), (980, 290), (980, 385), (830, 385)],  # Middle-Right Callout (4X) + GD&T
    [(245, 875), (400, 875), (400, 965), (245, 965)],  # Bottom-Left Callout (5X)
    [(730, 735), (990, 735), (990, 985), (730, 985)]  # Title Block
]

img_width, img_height = my_image.size

# Scale coordinates from 0-1000 back to actual image pixels
corners_set = scale_back(img_width, img_height, corners_set)

# Draw the rectangle and show
result_image = draw_red_rectangle(my_image, corners_set)
print("\n\n*********************************************************\n\n")

crop_and_save_areas(image_path, corners_set)