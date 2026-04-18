#!/usr/bin/env python3
"""Create a simple icon for the Implementation Queue app"""

import os

# Create Resources directory
os.makedirs("/usr/local/share/universal-memory-system/ImplementationQueue.app/Contents/Resources", exist_ok=True)

# Create a simple icon using emoji (rocket)
icon_script = """
# Create icon from emoji
convert -background none -fill black -font "Apple-Color-Emoji" -pointsize 512 \
    -gravity center label:"🚀" \
    /tmp/impl_queue_icon.png 2>/dev/null || \
echo "🚀" > /usr/local/share/universal-memory-system/ImplementationQueue.app/Contents/Resources/icon.txt
"""

os.system(icon_script)
print("✅ Icon placeholder created")