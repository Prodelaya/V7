
from PIL import Image, ImageChops, ImageEnhance
from pathlib import Path
import random

def create_glitch_gif(input_path, output_path, frames=10):
    """Generates a glitchy GIF from an input image."""
    try:
        original = Image.open(input_path).convert("RGBA")
        width, height = original.size
        
        # Resize if too huge (Telegram limit)
        if width > 512:
            ratio = 512 / width
            new_height = int(height * ratio)
            original = original.resize((512, new_height), Image.Resampling.LANCZOS)
            width, height = original.size

        gif_frames = []
        
        for _ in range(frames):
            # Create a copy
            frame = original.copy()
            
            # 1. RGB Shift
            r, g, b, a = frame.split()
            
            shift_x = random.randint(-5, 5)
            shift_y = random.randint(-5, 5)
            
            r = ImageChops.offset(r, shift_x, shift_y)
            b = ImageChops.offset(b, -shift_x, -shift_y)
            
            frame = Image.merge("RGBA", (r, g, b, a))
            
            # 2. Random blocks (noise)
            # Create a new layer for noise
            noise = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            # Just add simple noise blocks not fully implemented for simplicity/speed
            # Let's just adjust brightness randomly for flickering
            
            enhancer = ImageEnhance.Brightness(frame)
            frame = enhancer.enhance(random.uniform(0.8, 1.2))
            
            # Convert to RGB for GIF (transparency can be tricky, stick to RGB with black bg if needed)
            # But let's try to keep it simple.
            bg = Image.new("RGB", frame.size, (10, 10, 15)) # Dark background
            bg.paste(frame, mask=frame.split()[3])
            
            gif_frames.append(bg)

        # Save
        gif_frames[0].save(
            output_path,
            save_all=True,
            append_images=gif_frames[1:],
            duration=100,
            loop=0
        )
        print(f"GIF created at {output_path}")
        return True
    
    except Exception as e:
        print(f"Error creating GIF: {e}")
        return False

if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent
    create_glitch_gif(
        str(base_dir / "src/subscriptions/infrastructure/telegram/media/logo.png"),
        str(base_dir / "src/subscriptions/infrastructure/telegram/media/welcome_glitch.gif")
    )
