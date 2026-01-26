# Venus OS Custom Sensors

Custom tank and environmental sensors for Venus OS on Raspberry Pi.

## Features

- **Multi-Tank Sensor**: Up to 4 tank inputs (A0-A3) via Arduino Mega
  - 15-second rolling average for stable readings
  - Auto-detect: Ground input to disable tank
  - Configurable capacity, fluid type, and name from GUI

- **BME280 Sensor**: Temperature, humidity, and pressure via I2C
  - Pressure displayed in sensor name (e.g., "Baro (1013.2 hPa)")

## Hardware Required

- Raspberry Pi 4B with Venus OS
- Arduino Mega 2560
- BME280 sensor module
- 2x USB-TTL converters (FTDI FT232R recommended)
- **Powered USB hub** (required - Pi can't power both converters during boot)

## Installation

### Step 1: Clone the repository
```bash
cd /data
git clone https://github.com/TheMasterOfNone-NZ/Venus-Sensors.git venus-sensors
```

If git is not installed:
```bash
opkg update
opkg install git
```

### Step 2: Run the installer
```bash
cd /data/venus-sensors
chmod +x install.sh
./install.sh
```

### Step 3: Upload Arduino code

Upload `arduino/multi_tank_sensor.ino` to your Arduino Mega using the Arduino IDE.

### Step 4: Reboot
```bash
reboot
```

## Wiring

### Tank Sensor (Arduino Mega)

| Arduino Pin | Connection |
|-------------|------------|
| A0 | Tank 0 sensor (0-5V) |
| A1 | Tank 1 sensor (0-5V) |
| A2 | Tank 2 sensor (0-5V) |
| A3 | Tank 3 sensor (0-5V) |
| Pin 14 (TX3) | USB-TTL RX |
| GND | USB-TTL GND |

**Note:** Ground an input (connect to GND) to disable that tank.

### BME280 (Raspberry Pi I2C)

| BME280 Pin | Pi Pin |
|------------|--------|
| VIN | 3.3V (Pin 1) |
| GND | GND (Pin 6) |
| SDA | SDA (Pin 3 / GPIO2) |
| SCL | SCL (Pin 5 / GPIO3) |

### USB Ports

The USB-TTL converters must be plugged into consistent USB ports:

| USB Port | Device |
|----------|--------|
| Port 1-1.3 | Tank sensor (ignored by Venus OS) |
| Port 1-1.4 | VE.Bus or other Victron device |

**Important:** Use a powered USB hub for both converters.

## Configuration

### Tank Settings

Edit `/data/dbus-tank-sensor/settings.json`:
```json
{
  "tanks": [
    {"capacity": 100.0, "fluid_type": 1, "custom_name": "Fresh Water"},
    {"capacity": 100.0, "fluid_type": 0, "custom_name": "Fuel"},
    {"capacity": 100.0, "fluid_type": 2, "custom_name": "Waste Water"},
    {"capacity": 100.0, "fluid_type": 5, "custom_name": "Black Water"}
  ]
}
```

Fluid types:
- 0 = Fuel
- 1 = Fresh Water
- 2 = Waste Water
- 3 = Live Well
- 4 = Oil
- 5 = Black Water

Settings can also be changed from the Venus OS GUI.

### Arduino Calibration

Edit these values in the Arduino code for your sensors:
```cpp
const float TANK_EMPTY_VOLTAGE[4] = {0.5, 0.5, 0.5, 0.5};   // Voltage when empty
const float TANK_FULL_VOLTAGE[4] = {4.5, 4.5, 4.5, 4.5};    // Voltage when full
```

## Commands
```bash
# Check service status
svstat /service/tank-sensor
svstat /service/bme280

# Restart services
svc -t /service/tank-sensor
svc -t /service/bme280

# View tank values
dbus -y com.victronenergy.tank.tank0 / GetValue

# View BME280 values
dbus -y com.victronenergy.temperature.bme280_temp / GetValue
```

## Troubleshooting

### Services not starting after reboot

Check that `/data/rc.local` exists and is executable:
```bash
cat /data/rc.local
chmod +x /data/rc.local
```

### Pi won't boot with USB-TTL converters

Use a powered USB hub. The Pi 4 cannot supply enough power to both converters during boot.

### Tank not showing in GUI

1. Check the Arduino is sending data: Look at Serial Monitor (115200 baud)
2. Check the input isn't grounded (grounded = disabled)
3. Restart the service: `svc -t /service/tank-sensor`

### Wrong USB port assignments

Check current assignments:
```bash
udevadm info -n /dev/ttyUSB0 | grep DEVPATH
udevadm info -n /dev/ttyUSB1 | grep DEVPATH
```

Update `/etc/udev/rules.d/serial-starter.rules` if needed.

## File Locations

| File | Purpose |
|------|---------|
| `/data/dbus-tank-sensor/tank_service.py` | Tank sensor service |
| `/data/dbus-tank-sensor/settings.json` | Tank settings |
| `/data/dbus-bme280/bme280_service.py` | BME280 service |
| `/data/service/tank-sensor/run` | Tank service runner |
| `/data/service/bme280/run` | BME280 service runner |
| `/data/rc.local` | Boot script |
| `/etc/udev/rules.d/serial-starter.rules` | USB port rules |

## License

MIT License
