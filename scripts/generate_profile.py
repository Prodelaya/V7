from PIL import Image
from pathlib import Path

def create_profile_pic():
    # 1. Config
    size = (1000, 1000)
    # No external BG image, just solid color
    bg_color = (10, 10, 10, 255) # Almost black
    base_dir = Path(__file__).parent.parent
    logo_path = base_dir / "src/web/static/img/logo_sketchy.png"
    output_path = base_dir / "src/web/static/img/retador_telegram_profile.png"

    # 2. Create Solid Background
    bg = Image.new("RGBA", size, bg_color)

    # 3. Add Logo
    try:
        logo = Image.open(logo_path).convert("RGBA")
        
        # Logo size: 80% of width
        logo_width = int(size[0] * 0.8)
        ratio = logo_width / float(logo.size[0])
        logo_height = int(float(logo.size[1]) * ratio)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Center position
        x = (size[0] - logo_width) // 2
        y = (size[1] - logo_height) // 2
        
        bg.paste(logo, (x, y), logo)
    except Exception as e:
        print(f"Error loading logo: {e}")

    # 4. Save
    bg.save(output_path)
    print(f"Profile picture saved to {output_path}")

if __name__ == "__main__":
    create_profile_pic()
