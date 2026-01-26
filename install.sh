#!/bin/sh
# Venus OS Custom Sensors Installer
# Installs: Multi-Tank Sensor, BME280 Temperature/Humidity/Pressure

echo "=========================================="
echo "Venus OS Custom Sensors Installer"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check we're running on Venus OS
if [ ! -d "/opt/victronenergy" ]; then
    echo "ERROR: This script must be run on Venus OS"
    exit 1
fi

# Create directories
echo "Creating directories..."
mkdir -p /data/dbus-tank-sensor
mkdir -p /data/dbus-bme280
mkdir -p /data/service/tank-sensor
mkdir -p /data/service/bme280

# Copy tank sensor files
echo "Installing tank sensor..."
cp "$SCRIPT_DIR/tank-sensor/tank_service.py" /data/dbus-tank-sensor/
chmod +x /data/dbus-tank-sensor/tank_service.py

# Only copy settings if it doesn't exist (preserve user settings)
if [ ! -f /data/dbus-tank-sensor/settings.json ]; then
    cp "$SCRIPT_DIR/tank-sensor/settings.json" /data/dbus-tank-sensor/
fi

cp "$SCRIPT_DIR/tank-sensor/run" /data/service/tank-sensor/
chmod +x /data/service/tank-sensor/run

# Copy BME280 files
echo "Installing BME280 sensor..."
cp "$SCRIPT_DIR/bme280/bme280_service.py" /data/dbus-bme280/
chmod +x /data/dbus-bme280/bme280_service.py
cp "$SCRIPT_DIR/bme280/run" /data/service/bme280/
chmod +x /data/service/bme280/run

# Install rc.local
echo "Installing rc.local..."
cp "$SCRIPT_DIR/rc.local" /data/rc.local
chmod +x /data/rc.local

# Install udev rules
echo "Installing udev rules..."
cp "$SCRIPT_DIR/udev/serial-starter.rules" /etc/udev/rules.d/serial-starter.rules
udevadm control --reload-rules

# Create service links
echo "Creating service links..."
ln -sf /data/service/tank-sensor /service/tank-sensor
ln -sf /data/service/bme280 /service/bme280

# Start services
echo "Starting services..."
svc -t /service/tank-sensor 2>/dev/null
svc -t /service/bme280 2>/dev/null

# Wait for services to start
sleep 3

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Services:"
svstat /service/tank-sensor 2>/dev/null || echo "tank-sensor: not running yet"
svstat /service/bme280 2>/dev/null || echo "bme280: not running yet"
echo ""
echo "Next steps:"
echo "1. Upload Arduino code from arduino/multi_tank_sensor.ino"
echo "2. Reboot: reboot"
echo ""
echo "For troubleshooting, see README.md"
