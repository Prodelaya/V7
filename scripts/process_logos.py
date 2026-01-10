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
    ("sportiumlogo.png", "sportium.png", "sportium_red"), # Fondo Rojo, Letra Blanca force
    ("b365 logo.jpg", "bet365.png", "make_white"),        # Texto Blanco
    ("bwinlogo.png", "bwin.png", "make_white"),           # Texto Blanco
    
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
    Sportium: Keep Red background, Force Text to White.
    Target Red: ~ (227, 6, 19).
    Logic:
    1. If pixel is roughly RED -> Keep Red (or enhance to pure sportium red).
    2. If pixel is roughly WHITE (bg) -> Transparent.
    3. If pixel is ANYTHING ELSE (text is usually black/grey in some versions, or white, or transparent) -> FORCE WHITE.
    Wait, original image `sportiumlogo.png` likely has Red box and White letters.
    The user said: "me has vuelto a poner el logo de sportium con fondo rojo y 'sin fondo' en las letras".
    This means the letters are transparent holes.
    So:
    1. Identify RED pixels -> Keep RED.
    2. Identify TRANSPARENT or HOLE pixels inside the red box -> Make them WHITE.
    
    BUT, if I'm processing the original raw image again...
    Assuming original is: Red Rect + White Text + White BG outside.
    My previous `sportium_red` might have removed the white text making it transparent.
    """
    img = img.convert("RGBA")
    
    # First remove outer white background
    datas = img.getdata()
    new_data = []
    
    for item in datas:
        r, g, b, a = item
        
        # Is it White Background? (High R, G, B)
        if r > 220 and g > 220 and b > 220:
             new_data.append((255, 255, 255, 0)) # Transparent
        
        # Is it Red? (High R, Low G/B)
        elif r > 150 and g < 100 and b < 100:
            new_data.append(item) # Keep Red
            
        # Is it the Text? (If it was white, we effectively removed it above). 
        # Ah, if the text is WHITE in the original, `remove_white` logic kills it.
        # We need to distinguish "White Text inside Red" vs "White Background outside".
        # This is hard without flood fill.
        
        # Alternative: If the user says "letters lack background", maybe they are transparent holes.
        # So, if I see transparency (after some processing) I should fill it? No.
        
        # Let's try:
        # If it is NOT Red and NOT White-BG -> It must be text?
        # If original text is White, it matches White-BG condition.
        # TRICK: Sportium red is usually a box.
        # Let's just assume we want to turn the transparent parts back to white? No.
        
        # New strategy:
        # 1. Detect Red Box.
        # 2. Inside Red Box, make everything else White.
        # But honestly, without computer vision, differentiating 'White Text' from 'White BG' is tricky if they are connected.
        # Usually logos have a gap.
        
        # Simple Fix: Assuming text is distinct.
        # If pixel is PURE WHITE -> It's text (keep it 255,255,255,255).
        # But wait, BG is also white.
        # Trim first?
        # Let's just use a crop logic or "central white is text".
        # Or, usually Sportium logo file has a slight difference.
        
        # Let's try this:
        # Keep everything. Just Trim.
        # If user provided a file with White BG, Red Box, White Text...
        # I will simply TRIM the image first (removing outer white).
        # Any white remaining inside is text.
        
        else:
             # Whatever else (dark text?), make it White
             new_data.append((255, 255, 255, 255))
             
    # This logic is flawed if text is white.
    # Let's do:
    # 1. Trim White borders.
    # 2. Then any white remaining is text.
    pass 

    img2 = trim(img) # This removes surrounding white if it touches edges.
    
    # Now process pixels of trimmed image
    datas = img2.getdata()
    new_data = []
    for item in datas:
        r,g,b,a = item
        # If white (or close), keep it White (Text)
        if r > 200 and g > 200 and b > 200:
             new_data.append((255, 255, 255, 255))
        # If red, keep red
        elif r > 150 and g < 100:
             new_data.append(item)
        else:
             # Make transparent (outer artifacts)
             new_data.append((255, 255, 255, 0))
             
    img2.putdata(new_data)
    return img2

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
