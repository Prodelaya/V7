import os
from PIL import Image
import numpy as np

SOURCE_DIR = "src/web/static/img"
TARGET_FILES = {
    # White background removal
    "b365 logo.jpg": "bet365.png",
    "sportiumlogo.png": "sportium.png",
    "winamaxlogo.png": "winamax.png",
    "coderelogo.png": "codere.png",
    "bwinlogo.png": "bwin.png",
    "yaasslogo.jpg": "yaass.png"
}

NEON_LOGO_SOURCE = "logo_neon.png"
NEON_LOGO_TARGET = "logo_final.png"

def remove_white_bg(img):
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

def black_to_transparent(img):
    """
    Converts black background to transparent relying on brightness.
    Perfect for neon on black.
    """
    img = img.convert("RGBA")
    data = np.array(img)
    
    # Calculate brightness
    r, g, b, a = data.T
    brightness = (r + g + b) // 3
    
    # Set alpha based on brightness (Black pixels become transparent)
    # Adjust threshold as needed. pure black is 0.
    # We want to keep bright colors opaque.
    
    # Simple logic: if pixel is very dark, reduce alpha.
    # Actually, for neon on black, we can use the max channel intensity as alpha?
    # Let's try a simple threshold first.
    
    # Better approach for "glow":
    # Alpha = max(R, G, B)
    new_alpha = np.max(data[:, :, :3], axis=2)
    
    # Enhance alpha to make the core neon solid
    new_alpha = np.clip(new_alpha * 1.5, 0, 255).astype(np.uint8)
    
    data[:, :, 3] = new_alpha
    return Image.fromarray(data)

def process_images():
    print("Processing standard logos (White removal)...")
    for source, target in TARGET_FILES.items():
        source_path = os.path.join(SOURCE_DIR, source)
        target_path = os.path.join(SOURCE_DIR, target)
        
        if os.path.exists(source_path):
            try:
                img = Image.open(source_path)
                img = remove_white_bg(img)
                img.save(target_path, "PNG")
                print(f"Processed: {source} -> {target}")
            except Exception as e:
                print(f"Error processing {source}: {e}")
        else:
            print(f"Skipped (Not Found): {source}")

    print("Processing Neon Logo (Black removal)...")
    source_path = os.path.join(SOURCE_DIR, NEON_LOGO_SOURCE)
    target_path = os.path.join(SOURCE_DIR, NEON_LOGO_TARGET)
    if os.path.exists(source_path):
        try:
            img = Image.open(source_path)
            img = black_to_transparent(img)
            img.save(target_path, "PNG")
            print(f"Processed Neon: {source_path} -> {target_path}")
        except Exception as e:
            print(f"Error processing Neon Logo: {e}")

if __name__ == "__main__":
    process_images()
