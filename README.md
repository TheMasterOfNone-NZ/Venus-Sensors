# Venus OS Custom Sensors

Custom tank and environmental sensors for Venus OS.

## Hardware

- Raspberry Pi 4B with Venus OS
- Arduino Mega 2560 (tank sensors on A0-A3)
- BME280 on Pi I2C (address 0x76)
- 2x USB-TTL converters (via powered USB hub)

## Sensors

### Multi-Tank Sensor (Arduino)
- 4 tank inputs (A0-A3)
- Ground input to disable tank
- 15-second rolling average
- Auto-detect connected sensors

### BME280
- Temperature (°C)
- Humidity (%)
- Pressure (hPa) - shown in sensor name

## Installation
```bash
cd /data/venus-sensors
./install.sh
```

## Arduino

Upload the code from `arduino/multi_tank_sensor.ino` to your Arduino Mega.

## Wiring

### Tank Sensor (Arduino)
- A0-A3: Tank sensor inputs (0-5V)
- Pin 14 (TX3): USB-TTL RX
- GND: USB-TTL GND

### BME280 (Pi I2C)
- VIN: Pi 3.3V (pin 1)
- GND: Pi GND (pin 6)
- SDA: Pi SDA (pin 3)
- SCL: Pi SCL (pin 5)

## USB Port Assignment

- Port 1-1.3: Tank sensor (ttyTANK)
- Port 1-1.4: VE.Bus (mkx)

## Commands
```bash
# Check services
svstat /service/tank-sensor
svstat /service/bme280

# Restart services
svc -t /service/tank-sensor
svc -t /service/bme280

# View values
dbus -y com.victronenergy.tank.tank0 / GetValue
dbus -y com.victronenergy.temperature.bme280_temp / GetValue
```
# Venus-Sensors
