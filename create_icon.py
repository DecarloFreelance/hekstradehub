#!/usr/bin/env python3
"""
Create a simple PNG icon for the trading dashboard
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    
    # Create 256x256 icon
    size = 256
    img = Image.new('RGB', (size, size), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Draw background gradient effect
    for i in range(size):
        color_val = int(26 + (i / size) * 20)
        draw.rectangle([(0, i), (size, i+1)], fill=(color_val, color_val, 46))
    
    # Draw chart-like elements
    # Green upward line (profit)
    draw.line([(40, 180), (80, 140), (120, 160), (160, 100), (200, 80)], 
              fill='#00ff88', width=8)
    
    # Draw candlesticks
    candles = [
        (50, 150, 160, '#00ff88'),   # Green candle
        (90, 120, 150, '#ff4444'),   # Red candle
        (130, 140, 170, '#00ff88'),  # Green candle
        (170, 90, 130, '#00ff88'),   # Green candle
        (210, 70, 100, '#00ff88'),   # Green candle
    ]
    
    for x, top, bottom, color in candles:
        # Wick
        draw.line([(x, top-10), (x, bottom+10)], fill=color, width=2)
        # Body
        draw.rectangle([(x-6, top), (x+6, bottom)], fill=color)
    
    # Draw border
    draw.rectangle([(0, 0), (size-1, size-1)], outline='#00ff88', width=4)
    
    # Add text "LIVE"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    text = "LIVE"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Draw text with shadow
    text_x = (size - text_width) // 2
    text_y = size - 70
    
    draw.text((text_x+2, text_y+2), text, fill='#000000', font=font)  # Shadow
    draw.text((text_x, text_y), text, fill='#00ff88', font=font)  # Text
    
    # Save icon
    img.save('/home/hektic/hekstradehub/dashboard_icon.png')
    print("✅ Icon created: dashboard_icon.png")
    
    # Also save smaller versions for different uses
    img_small = img.resize((128, 128), Image.Resampling.LANCZOS)
    img_small.save('/home/hektic/hekstradehub/dashboard_icon_128.png')
    
    img_tiny = img.resize((64, 64), Image.Resampling.LANCZOS)
    img_tiny.save('/home/hektic/hekstradehub/dashboard_icon_64.png')
    
    print("✅ Created multiple sizes: 256px, 128px, 64px")

except ImportError:
    print("⚠️  PIL/Pillow not installed. Creating simple fallback icon...")
    
    # Create a simple SVG icon as fallback
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#1a1a2e" rx="20"/>
  <rect x="4" y="4" width="248" height="248" fill="none" stroke="#00ff88" stroke-width="8" rx="16"/>
  
  <!-- Chart line -->
  <polyline points="40,180 80,140 120,160 160,100 200,80" 
            fill="none" stroke="#00ff88" stroke-width="6" stroke-linecap="round"/>
  
  <!-- Candlesticks -->
  <line x1="50" y1="140" x2="50" y2="170" stroke="#00ff88" stroke-width="3"/>
  <rect x="44" y="150" width="12" height="20" fill="#00ff88"/>
  
  <line x1="90" y1="110" x2="90" y2="160" stroke="#ff4444" stroke-width="3"/>
  <rect x="84" y="120" width="12" height="30" fill="#ff4444"/>
  
  <line x1="130" y1="130" x2="130" y2="180" stroke="#00ff88" stroke-width="3"/>
  <rect x="124" y="140" width="12" height="30" fill="#00ff88"/>
  
  <line x1="170" y1="80" x2="170" y2="140" stroke="#00ff88" stroke-width="3"/>
  <rect x="164" y="90" width="12" height="40" fill="#00ff88"/>
  
  <line x1="210" y1="60" x2="210" y2="110" stroke="#00ff88" stroke-width="3"/>
  <rect x="204" y="70" width="12" height="30" fill="#00ff88"/>
  
  <!-- "LIVE" text -->
  <text x="128" y="220" font-family="Arial, sans-serif" font-size="42" 
        font-weight="bold" fill="#00ff88" text-anchor="middle">LIVE</text>
</svg>'''
    
    with open('/home/hektic/hekstradehub/dashboard_icon.svg', 'w') as f:
        f.write(svg_content)
    
    print("✅ Created SVG icon: dashboard_icon.svg")
    print("ℹ️  Install Pillow for PNG icons: pip install Pillow")
    
    # Try to convert SVG to PNG using system tools
    import subprocess
    try:
        subprocess.run([
            'convert', 
            '/home/hektic/hekstradehub/dashboard_icon.svg',
            '/home/hektic/hekstradehub/dashboard_icon.png'
        ], check=True, capture_output=True)
        print("✅ Converted to PNG using ImageMagick")
    except:
        print("ℹ️  To convert SVG to PNG, install: sudo apt install imagemagick")
        print("ℹ️  Or install Pillow: pip install Pillow")
