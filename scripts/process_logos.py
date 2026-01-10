import os
from PIL import Image, ImageOps, ImageChops
import numpy as np

SOURCE_DIR = "src/web/static/img"

# Mapeo de archivos y funciones a aplicar
CONFIG = [
    # (Source, Target, Method)
    
    # Standard White Removal
    ("winamaxlogo.png", "winamax.png", "remove_white"),
    ("coderelogo.png", "codere.png", "remove_white"),
    ("yaasslogo.jpg", "yaass.png", "remove_white"),
    ("retabetlogo.png", "retabet.png", "remove_white"),
    ("versuslogo.png", "versus.png", "remove_white"),

    # Special Cases
    ("sportiumlogo.png", "sportium.png", "sportium_red"), # Fondo Rojo, Letra Blanca
    ("b365 logo.jpg", "bet365.png", "make_white"),        # Texto Blanco (Invertir/Forzar)
    ("bwinlogo.png", "bwin.png", "make_white"),           # Texto Blanco
    ("pokerstarslogo.png", "pokerstars.png", "crop_remove_white"), # Recortar margen + quitar blanco
    
    # Main Logo
    ("logo_v5.png", "logo_final.png", "neon_black_to_alpha"),
    ("logo_v5.png", "logo_bg.png", "neon_black_to_alpha"),
]

def trim(im):
    """Autocrop image removing empty borders"""
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)
    return im

def remove_white_bg(img):
    img = img.convert("RGBA")
    datas = img.getdata()
    new_data = []
    for item in datas:
        # If white-ish, make transparent
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    return img

def make_white_text(img):
    """
    Turns non-white pixels into pure white. Keeps transparency.
    If image has white background, remove it first.
    """
    img = img.convert("RGBA")
    # First, simple white removal if it's a solid block
    img = remove_white_bg(img)
    
    datas = img.getdata()
    new_data = []
    for item in datas:
        # If transparent, keep transparent
        if item[3] == 0:
            new_data.append(item)
        else:
            # If visible, make it white
            new_data.append((255, 255, 255, 255))
    img.putdata(new_data)
    return img

def sportium_red(img):
    """
    Sportium: Keep Red background, Ensure text is white.
    Original usually has Red BG and White Text.
    We just need to ensure no outer white box exists, but keep the red box.
    """
    img = img.convert("RGBA")
    # If the source has a massive white canvas around the red box, remove it.
    # We assume 'white' is background. Red is content.
    datas = img.getdata()
    new_data = []
    for item in datas:
        # If white, transparent
        if item[0] > 230 and item[1] > 230 and item[2] > 230:
            new_data.append((255, 255, 255, 0))
        else:
            # Keep original colors (Red bg, white text)
            new_data.append(item)
    img.putdata(new_data)
    # Trim to remove excess transparent space
    img = trim(img)
    return img

def neon_black_to_alpha(img):
    """
    Logo V5: Black to Transparent.
    """
    img = img.convert("RGBA")
    data = np.array(img)
    # Alpha = Max(R,G,B)
    new_alpha = np.max(data[:, :, :3], axis=2)
    # Boost alpha
    new_alpha = np.clip(new_alpha * 2.0, 0, 255).astype(np.uint8)
    data[:, :, 3] = new_alpha
    return Image.fromarray(data)

def crop_remove_white(img):
    """Remove white bg then TRIM aggressively"""
    img = remove_white_bg(img)
    img = trim(img)
    return img

def process_images():
    print("Starting V5 Image Processing...")
    
    for source, target, method_name in CONFIG:
        source_path = os.path.join(SOURCE_DIR, source)
        target_path = os.path.join(SOURCE_DIR, target)
        
        if not os.path.exists(source_path):
            print(f"MISSING: {source}")
            continue
            
        try:
            img = Image.open(source_path)
            
            if method_name == "remove_white":
                img = remove_white_bg(img)
            elif method_name == "make_white":
                img = make_white_text(img)
            elif method_name == "sportium_red":
                img = sportium_red(img)
            elif method_name == "neon_black_to_alpha":
                img = neon_black_to_alpha(img)
            elif method_name == "crop_remove_white":
                img = crop_remove_white(img)
                
            img.save(target_path, "PNG")
            print(f"Processed [{method_name}]: {source} -> {target}")
            
        except Exception as e:
            print(f"ERROR {source}: {e}")

if __name__ == "__main__":
    process_images()
