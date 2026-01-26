#!/usr/bin/env python3
"""
BME280 Service for Venus OS
Displays temperature with pressure in the name
"""
import sys
import os
import time
import struct
from fcntl import ioctl

sys.path.insert(1, '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python')
from vedbus import VeDbusService
from gi.repository import GLib
import dbus.mainloop.glib

I2C_PORT = 1
I2C_ADDRESS = 0x76
I2C_SLAVE = 0x0703

class BME280:
    """Pure Python BME280 driver using direct I2C access"""
    
    def __init__(self, bus=1, address=0x76):
        self.bus = bus
        self.address = address
        self.i2c = None
        
        self._open()
        self._load_calibration()
        self._configure()
    
    def _open(self):
        if self.i2c:
            try:
                self.i2c.close()
            except:
                pass
        self.i2c = open(f'/dev/i2c-{self.bus}', 'rb+', buffering=0)
        ioctl(self.i2c, I2C_SLAVE, self.address)
    
    def _configure(self):
        self._write_byte(0xF2, 0x05)
        self._write_byte(0xF4, 0xB7)
        self._write_byte(0xF5, 0x00)
    
    def _write_byte(self, reg, value):
        self.i2c.write(bytes([reg, value]))
    
    def _read_bytes(self, reg, length):
        self.i2c.write(bytes([reg]))
        return self.i2c.read(length)
    
    def _load_calibration(self):
        cal1 = self._read_bytes(0x88, 26)
        cal2 = self._read_bytes(0xA1, 1)
        cal3 = self._read_bytes(0xE1, 7)
        
        self.dig_T1 = struct.unpack('<H', cal1[0:2])[0]
        self.dig_T2 = struct.unpack('<h', cal1[2:4])[0]
        self.dig_T3 = struct.unpack('<h', cal1[4:6])[0]
        
        self.dig_P1 = struct.unpack('<H', cal1[6:8])[0]
        self.dig_P2 = struct.unpack('<h', cal1[8:10])[0]
        self.dig_P3 = struct.unpack('<h', cal1[10:12])[0]
        self.dig_P4 = struct.unpack('<h', cal1[12:14])[0]
        self.dig_P5 = struct.unpack('<h', cal1[14:16])[0]
        self.dig_P6 = struct.unpack('<h', cal1[16:18])[0]
        self.dig_P7 = struct.unpack('<h', cal1[18:20])[0]
        self.dig_P8 = struct.unpack('<h', cal1[20:22])[0]
        self.dig_P9 = struct.unpack('<h', cal1[22:24])[0]
        
        self.dig_H1 = cal2[0]
        self.dig_H2 = struct.unpack('<h', cal3[0:2])[0]
        self.dig_H3 = cal3[2]
        self.dig_H4 = (cal3[3] << 4) | (cal3[4] & 0x0F)
        self.dig_H5 = (cal3[5] << 4) | ((cal3[4] >> 4) & 0x0F)
        self.dig_H6 = struct.unpack('<b', bytes([cal3[6]]))[0]
    
    def read(self):
        data = self._read_bytes(0xF7, 8)
        
        raw_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_temp = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        raw_hum = (data[6] << 8) | data[7]
        
        var1 = (((raw_temp >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((raw_temp >> 4) - self.dig_T1) * ((raw_temp >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        t_fine = var1 + var2
        temperature = ((t_fine * 5 + 128) >> 8) / 100.0
        
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        
        if var1 == 0:
            pressure = 0
        else:
            p = 1048576 - raw_press
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
            var2 = (self.dig_P8 * p) >> 19
            pressure = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
            pressure = pressure / 25600.0
        
        h = t_fine - 76800
        h = (((((raw_hum << 14) - (self.dig_H4 << 20) - (self.dig_H5 * h)) + 16384) >> 15) *
             (((((((h * self.dig_H6) >> 10) * (((h * self.dig_H3) >> 11) + 32768)) >> 10) + 2097152) *
               self.dig_H2 + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.dig_H1) >> 4)
        h = max(0, min(h, 419430400))
        humidity = (h >> 12) / 1024.0
        
        return temperature, pressure, humidity


class BME280Service:
    def __init__(self):
        self.bme280 = BME280(I2C_PORT, I2C_ADDRESS)
        
        self.service = VeDbusService('com.victronenergy.temperature.bme280_temp', register=False)
        self.service.add_path('/Mgmt/ProcessName', 'bme280_service')
        self.service.add_path('/Mgmt/ProcessVersion', '1.0')
        self.service.add_path('/Mgmt/Connection', 'I2C')
        self.service.add_path('/DeviceInstance', 30)
        self.service.add_path('/ProductId', 0)
        self.service.add_path('/ProductName', 'BME280 Sensor')
        self.service.add_path('/FirmwareVersion', '1.0')
        self.service.add_path('/Connected', 1)
        self.service.add_path('/Temperature', 0)
        self.service.add_path('/TemperatureType', 2)
        self.service.add_path('/CustomName', 'Baro', writeable=True)
        self.service.add_path('/Humidity', 0)
        self.service.add_path('/Pressure', 0)
        self.service.register()
        
        print('BME280 service started')
    
    def update(self):
        try:
            temperature, pressure, humidity = self.bme280.read()
            
            temperature = round(temperature, 1)
            pressure = round(pressure, 1)
            humidity = round(humidity, 1)
            
            self.service['/Temperature'] = temperature
            self.service['/Pressure'] = pressure
            self.service['/Humidity'] = humidity
            self.service['/CustomName'] = f'Baro ({pressure} hPa)'
            self.service['/Connected'] = 1
            
            print(f'Temp: {temperature}°C | Humidity: {humidity}% | Pressure: {pressure} hPa')
            
        except Exception as e:
            print(f'Error reading BME280: {e}')
            self.service['/Connected'] = 0
        
        return True


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    sensor = BME280Service()
    
    def poll():
        sensor.update()
        return True
    
    GLib.timeout_add(5000, poll)
    
    mainloop = GLib.MainLoop()
    mainloop.run()

if __name__ == '__main__':
    main()
