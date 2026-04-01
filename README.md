import cv2
import os

# Input & output folders
input_folder = "input_images"
output_folder = "mirrored_images"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Supported image formats
valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

# Loop through all files
for filename in os.listdir(input_folder):
    if filename.lower().endswith(valid_extensions):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        # Read image
        img = cv2.imread(input_path)

        if img is None:
            print(f"Skipping (can't read): {filename}")
            continue

        # Mirror (horizontal flip)
        mirrored = cv2.flip(img, 1)

        # Save image
        cv2.imwrite(output_path, mirrored)

        print(f"Processed: {filename}")

print("✅ All images mirrored successfully!")