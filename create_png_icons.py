#!/usr/bin/env python3
"""
Create PNG icons from SVG for better APK compatibility
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_png_icon(size, output_path):
    """Create a PNG icon with Fire Shakti branding"""
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background circle
    margin = size // 10
    draw.ellipse([margin, margin, size-margin, size-margin], 
                fill=(255, 68, 68, 255))  # #FF4444
    
    # Fire icon (simplified flame shape)
    flame_size = size // 3
    flame_x = size // 2 - flame_size // 2
    flame_y = size // 2 - flame_size // 2
    
    # Main flame
    draw.ellipse([flame_x, flame_y, flame_x + flame_size, flame_y + flame_size], 
                fill=(255, 215, 0, 255))  # Gold
    
    # Inner flame
    inner_size = flame_size // 2
    inner_x = flame_x + flame_size // 4
    inner_y = flame_y + flame_size // 4
    draw.ellipse([inner_x, inner_y, inner_x + inner_size, inner_y + inner_size], 
                fill=(255, 140, 0, 255))  # Orange
    
    # Text (for larger icons)
    if size >= 192:
        try:
            # Try to use a system font
            font_size = max(12, size // 20)
            font = ImageFont.load_default()
            text = "FIRE"
            
            # Get text size
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center text at bottom
            text_x = (size - text_width) // 2
            text_y = size - text_height - margin
            
            draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
        except:
            pass  # Skip text if font loading fails
    
    # Save PNG
    img.save(output_path, 'PNG')
    print(f"Created {output_path} ({size}x{size})")

def main():
    """Create all required PNG icons"""
    # Icon sizes for APK generation
    sizes = [48, 72, 96, 144, 192, 512]
    
    # Create icons directory if it doesn't exist
    icons_dir = "fire/static/icons"
    os.makedirs(icons_dir, exist_ok=True)
    
    # Create PNG icons
    for size in sizes:
        output_path = f"{icons_dir}/icon-{size}x{size}.png"
        create_png_icon(size, output_path)
    
    # Create special icons
    create_png_icon(180, f"{icons_dir}/apple-touch-icon.png")
    create_png_icon(32, f"{icons_dir}/favicon.png")
    
    print("\n✅ All PNG icons created successfully!")
    print("Icons created:")
    for size in sizes:
        print(f"  - icon-{size}x{size}.png")
    print("  - apple-touch-icon.png (180x180)")
    print("  - favicon.png (32x32)")

if __name__ == "__main__":
    main()
