#!/bin/bash
set -e

# Media Ingest Pi - One-liner Installer
# Usage: curl -sSL https://raw.githubusercontent.com/your-repo/media-ingest-pi/main/install.sh | bash

echo "=========================================="
echo "Media Ingest Pi - Installer"
echo "=========================================="
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This script is designed for Linux systems (Raspberry Pi)"
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "Error: Python 3.9 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

# Set installation directory
INSTALL_DIR="${INSTALL_DIR:-$HOME/media-ingest-pi}"

# Check if directory already exists
if [ -d "$INSTALL_DIR" ]; then
    echo "Warning: Directory $INSTALL_DIR already exists."
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
    rm -rf "$INSTALL_DIR"
fi

# Clone or download the repository
echo ""
echo "Downloading Media Ingest Pi..."
if command -v git &> /dev/null; then
    git clone https://github.com/bscholer/media-ingest-pi.git "$INSTALL_DIR"
else
    echo "Git not found, downloading zip..."
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    curl -sSL https://github.com/bscholer/media-ingest-pi/archive/main.zip -o main.zip
    unzip -q main.zip
    mv media-ingest-pi-main/* .
    rm -rf media-ingest-pi-main main.zip
fi

cd "$INSTALL_DIR"
echo "✓ Downloaded to $INSTALL_DIR"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt --user
echo "✓ Dependencies installed"

# Create necessary directories
echo ""
echo "Setting up directories..."
mkdir -p config
mkdir -p data
echo "✓ Created config and data directories"
echo "  (Configuration files will be created automatically on first run)"

# Make run script executable
if [ -f "run.sh" ]; then
    chmod +x run.sh
    echo "✓ Made run.sh executable"
fi

# Offer to install as systemd service
echo ""
read -p "Do you want to install as a systemd service (runs on boot)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Update service file with correct paths and ensure it runs as root
    SERVICE_FILE="media-ingest.service"
    if [ -f "$SERVICE_FILE" ]; then
        # Create a temporary service file with updated paths and User=root
        sed "s|/home/bscholer|$HOME|g" "$SERVICE_FILE" | \
        sed "s|^User=.*|User=root|g" | \
        sed "s|^Group=.*|Group=root|g" > /tmp/media-ingest.service
        
        sudo cp /tmp/media-ingest.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable media-ingest
        
        echo "✓ Service installed (runs as root for GPIO/LED access)"
        echo ""
        read -p "Do you want to start the service now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo systemctl start media-ingest
            echo "✓ Service started"
        fi
        
        rm /tmp/media-ingest.service
    fi
fi

# Check if we need sudo for port 80
PORT_WARNING=""
if grep -q "port: 80" config/settings.yaml 2>/dev/null; then
    PORT_WARNING="Note: Running on port 80 requires root/sudo privileges."
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start the service:"
if systemctl is-enabled media-ingest &>/dev/null; then
    echo "   sudo systemctl status media-ingest"
else
    echo "   cd $INSTALL_DIR"
    if [ -n "$PORT_WARNING" ]; then
        echo "   sudo python3 src/main.py"
    else
        echo "   python3 src/main.py"
    fi
fi
echo ""
echo "2. Access the web interface and complete setup:"
echo "   http://$(hostname -I | awk '{print $1}')"
echo ""
echo "   Configure your settings, MQTT, and device profiles in the web UI!"
echo ""
if [ -n "$PORT_WARNING" ]; then
    echo "$PORT_WARNING"
    echo ""
fi
echo "For more information, see README.md"
echo ""

