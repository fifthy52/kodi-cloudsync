#!/usr/bin/env python3
"""
Convert SVG icons to PNG format for Kodi
Requires: pip install Pillow cairosvg
"""

try:
    import cairosvg
    from PIL import Image
    import io
    import os

    def svg_to_png(svg_path, png_path, size=128):
        """Convert SVG to PNG at specified size."""
        try:
            # Convert SVG to PNG bytes
            png_bytes = cairosvg.svg2png(url=svg_path, output_width=size, output_height=size)

            # Save PNG
            with open(png_path, 'wb') as f:
                f.write(png_bytes)

            print(f"✅ Created {png_path} ({size}x{size})")
            return True
        except Exception as e:
            print(f"❌ Error converting {svg_path}: {e}")
            return False

    def create_simple_png_fallback(png_path, color, text, size=128):
        """Create simple colored PNG with text as fallback."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create image with colored background
            img = Image.new('RGBA', (size, size), color)
            draw = ImageDraw.Draw(img)

            # Try to use default font
            try:
                font = ImageFont.truetype("arial.ttf", size//8)
            except:
                font = ImageFont.load_default()

            # Calculate text position
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (size - text_width) // 2
            y = (size - text_height) // 2

            # Draw text
            draw.text((x, y), text, fill='white', font=font)

            # Save
            img.save(png_path)
            print(f"✅ Created fallback {png_path} ({size}x{size})")
            return True
        except Exception as e:
            print(f"❌ Error creating fallback {png_path}: {e}")
            return False

    # Convert icons
    icons = [
        {
            'svg': 'service.cloudsync/resources/icon.svg',
            'png': 'service.cloudsync/resources/icon.png',
            'fallback_color': (33, 150, 243, 255),  # Blue
            'fallback_text': 'CS'
        },
        {
            'svg': 'repository.cloudsync/icon.svg',
            'png': 'repository.cloudsync/icon.png',
            'fallback_color': (117, 117, 117, 255),  # Gray
            'fallback_text': 'REPO'
        }
    ]

    print("🎨 Converting SVG icons to PNG...")

    for icon in icons:
        if os.path.exists(icon['svg']):
            # Try SVG conversion first
            if not svg_to_png(icon['svg'], icon['png']):
                # Fallback to simple colored PNG
                create_simple_png_fallback(
                    icon['png'],
                    icon['fallback_color'],
                    icon['fallback_text']
                )
        else:
            print(f"❌ SVG not found: {icon['svg']}")
            # Create fallback
            create_simple_png_fallback(
                icon['png'],
                icon['fallback_color'],
                icon['fallback_text']
            )

    print("\n📋 Next steps:")
    print("1. Check the generated PNG files")
    print("2. git add . && git commit -m 'Add icons'")
    print("3. git push for new release")

except ImportError as e:
    print("❌ Missing dependencies. Install with:")
    print("pip install Pillow cairosvg")
    print(f"Error: {e}")

    # Create basic fallback PNGs
    print("\n🔧 Creating basic fallback icons...")
    try:
        from PIL import Image, ImageDraw

        # CloudSync icon - blue circle with CS text
        img = Image.new('RGBA', (128, 128), (33, 150, 243, 255))
        draw = ImageDraw.Draw(img)
        draw.text((40, 50), "CS", fill='white')
        img.save('service.cloudsync/resources/icon.png')
        print("✅ Created basic service.cloudsync/resources/icon.png")

        # Repository icon - gray circle with REPO text
        img = Image.new('RGBA', (128, 128), (117, 117, 117, 255))
        draw = ImageDraw.Draw(img)
        draw.text((30, 50), "REPO", fill='white')
        img.save('repository.cloudsync/icon.png')
        print("✅ Created basic repository.cloudsync/icon.png")

    except ImportError:
        print("❌ Even Pillow is not available. Please install: pip install Pillow")