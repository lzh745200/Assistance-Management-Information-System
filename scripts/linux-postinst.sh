#!/bin/bash
# postinst script for assistance-management-system DEB package
# Runs after installation completes

set -e

# Determine install directory
INSTALL_DIR="/opt/assistance-management-system"

# Ensure backend binary is executable
if [ -f "$INSTALL_DIR/resources/backend/assistance-backend.exe" ]; then
    chmod +x "$INSTALL_DIR/resources/backend/assistance-backend.exe"
fi

# Ensure main Electron binary is executable
if [ -f "$INSTALL_DIR/assistance-management-system" ]; then
    chmod +x "$INSTALL_DIR/assistance-management-system"
fi

# Create user data directory if it doesn't exist
# (Electron app stores data in ~/.bumofu, created on first run)

# Update desktop database so the app appears in menu
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache /usr/share/icons/ 2>/dev/null || true
fi

# Install libgtk and other dependencies if missing (Kylin V10 may not have them)
# The deb depends line should handle this, but as fallback:
if ! dpkg -s libgtk-3-0 >/dev/null 2>&1; then
    apt-get install -y libgtk-3-0 libnotify4 libnss3 libxss1 libxtst6 2>/dev/null || true
fi

exit 0
