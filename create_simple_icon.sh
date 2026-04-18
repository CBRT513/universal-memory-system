#!/bin/bash

# Create a simple app icon for Universal Memory System
# This creates a blue gradient icon with "M" text

echo "Creating app icon for Universal Memory System..."

# Create iconset directory
ICONSET="AppIcon.iconset"
rm -rf "$ICONSET"
mkdir -p "$ICONSET"

# Create base SVG icon
cat > icon_base.svg << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#007AFF;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#005ACC;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" rx="225" fill="url(#grad1)"/>
  <text x="512" y="600" font-family="SF Pro Display, system-ui, Helvetica" font-size="420" fill="white" text-anchor="middle" font-weight="bold">M</text>
  <circle cx="512" cy="512" r="380" fill="none" stroke="white" stroke-width="40" opacity="0.3"/>
</svg>
EOF

# Function to create PNG from SVG using sips or other tools
create_png() {
    local size=$1
    local scale=$2
    local actual_size=$((size * scale))
    local suffix=""
    if [ $scale -gt 1 ]; then
        suffix="@${scale}x"
    fi
    local filename="icon_${size}x${size}${suffix}.png"
    
    echo "Creating $filename (${actual_size}x${actual_size})..."
    
    # Try using qlmanage first (built into macOS)
    qlmanage -t -s $actual_size -o "$ICONSET" icon_base.svg &>/dev/null
    
    if [ -f "$ICONSET/icon_base.svg.png" ]; then
        mv "$ICONSET/icon_base.svg.png" "$ICONSET/$filename"
    else
        # Fallback: create a simple blue square using Python
        python3 -c "
from PIL import Image, ImageDraw, ImageFont
import os

size = $actual_size
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw blue gradient background
for i in range(size):
    color = (0, int(122 - i * 30 / size), 255, 255)
    draw.rectangle([0, i, size, i+1], fill=color)

# Draw rounded corners
corner_radius = size // 5
draw.pieslice([0, 0, corner_radius*2, corner_radius*2], 180, 270, fill=(0, 0, 0, 0))
draw.pieslice([size-corner_radius*2, 0, size, corner_radius*2], 270, 360, fill=(0, 0, 0, 0))
draw.pieslice([0, size-corner_radius*2, corner_radius*2, size], 90, 180, fill=(0, 0, 0, 0))
draw.pieslice([size-corner_radius*2, size-corner_radius*2, size, size], 0, 90, fill=(0, 0, 0, 0))

# Draw 'M' text
try:
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', size=int(size * 0.4))
except:
    font = None

text = 'M'
if font:
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - size // 10
    draw.text((text_x, text_y), text, fill='white', font=font)

img.save('$ICONSET/$filename')
" 2>/dev/null || {
            # Final fallback: create using sips with a solid color
            echo "Using sips fallback for $filename"
            # Create a 1x1 blue pixel and scale it
            printf "\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x00\x00\x00\x00IEND\xaeB\`\x82" > temp_blue.png
            sips -z $actual_size $actual_size temp_blue.png --out "$ICONSET/$filename" &>/dev/null
            rm -f temp_blue.png
        }
    fi
}

# Generate all required icon sizes
create_png 16 1
create_png 16 2
create_png 32 1
create_png 32 2
create_png 128 1
create_png 128 2
create_png 256 1
create_png 256 2
create_png 512 1
create_png 512 2

# Create the .icns file
echo "Creating .icns file..."
iconutil -c icns "$ICONSET" -o AppIcon.icns 2>/dev/null || {
    echo "Warning: Could not create .icns file with iconutil"
    # Try alternative method
    if command -v makeicns &> /dev/null; then
        makeicns -in "$ICONSET/icon_512x512.png" -out AppIcon.icns
    else
        echo "Icon creation tools not available. App will use default icon."
    fi
}

# Move icon to Resources folder
if [ -f AppIcon.icns ]; then
    RESOURCES_PATH="Universal Memory System.app/Contents/Resources"
    mkdir -p "$RESOURCES_PATH"
    mv AppIcon.icns "$RESOURCES_PATH/AppIcon.icns"
    echo "Icon created and moved to $RESOURCES_PATH/AppIcon.icns"
else
    echo "Warning: Icon file was not created. App will use default icon."
fi

# Clean up
rm -rf "$ICONSET"
rm -f icon_base.svg
rm -f create_app_icon.py

echo "Icon creation complete!"