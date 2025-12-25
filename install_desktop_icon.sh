#!/bin/bash
# Install Trading Dashboard to system
# Creates desktop icon and menu entry

echo "🚀 Installing Trading Dashboard..."
echo ""

cd /home/hektic/hekstradehub

# Make scripts executable
chmod +x launch_dashboard.sh
chmod +x Trading-Dashboard.desktop

# Create icon if doesn't exist
if [ ! -f "dashboard_icon.png" ]; then
    echo "📸 Creating icon..."
    python create_icon.py
fi

# Install to desktop
echo "🖥️  Installing to Desktop..."
cp Trading-Dashboard.desktop ~/Desktop/
chmod +x ~/Desktop/Trading-Dashboard.desktop

# Install to applications menu
echo "📁 Installing to Applications Menu..."
mkdir -p ~/.local/share/applications
cp Trading-Dashboard.desktop ~/.local/share/applications/
chmod +x ~/.local/share/applications/Trading-Dashboard.desktop

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications/
fi

echo ""
echo "✅ Installation Complete!"
echo ""
echo "You can now:"
echo "  • Double-click 'Trading Dashboard' icon on your desktop"
echo "  • Find it in your applications menu under 'Finance'"
echo "  • Right-click the desktop icon → 'Allow Launching'"
echo ""
echo "To uninstall:"
echo "  rm ~/Desktop/Trading-Dashboard.desktop"
echo "  rm ~/.local/share/applications/Trading-Dashboard.desktop"
echo ""
