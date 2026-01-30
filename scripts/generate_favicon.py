from PIL import Image
from pathlib import Path

def create_favicon():
    base_dir = Path(__file__).parent.parent
    logo_path = base_dir / "src/web/static/img/logo_sketchy.png"
    output_path = base_dir / "src/web/static/favicon.ico"
    output_png_path = base_dir / "src/web/static/img/favicon.png"

    try:
        img = Image.open(logo_path).convert("RGBA")
        # Resize to standard favicon sizes
        img.save(output_path, format='ICO', sizes=[(32, 32), (64, 64)])
        
        # Also save a png version
        img_small = img.resize((64, 64), Image.Resampling.LANCZOS)
        img_small.save(output_png_path)
        
        print(f"Favicon saved to {output_path} and {output_png_path}")
    except Exception as e:
        print(f"Error creating favicon: {e}")

if __name__ == "__main__":
    create_favicon()
