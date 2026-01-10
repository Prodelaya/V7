import os
from PIL import Image
import numpy as np

SOURCE_DIR = "src/web/static/img"
TARGET_FILES = {
    "b365 logo.jpg": "bet365.png",
    "sportiumlogo.png": "sportium.png",
    "winamaxlogo.png": "winamax.png",
    "coderelogo.png": "codere.png",
    "bwinlogo.png": "bwin.png",
    "yaasslogo.jpg": "yaass.png"
}

def make_transparent(img):
    img = img.convert("RGBA")
    datas = img.getdata()
    new_data = []
    for item in datas:
        # Change all white (also shades of whites) to transparent
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    return img

def process_images():
    print("Processing images...")
    for source, target in TARGET_FILES.items():
        source_path = os.path.join(SOURCE_DIR, source)
        target_path = os.path.join(SOURCE_DIR, target)
        
        if os.path.exists(source_path):
            try:
                img = Image.open(source_path)
                img = make_transparent(img)
                img.save(target_path, "PNG")
                print(f"Processed: {source} -> {target}")
            except Exception as e:
                print(f"Error processing {source}: {e}")
        else:
            print(f"Skipped (Not Found): {source}")

if __name__ == "__main__":
    process_images()
