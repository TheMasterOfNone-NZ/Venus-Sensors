#!/usr/bin/env python3
"""
Multi-Tank Service for Venus OS
Uses separate processes for each tank
Ground input = OFF, otherwise shows level
"""
import serial
import time
import sys
import os
import json
import multiprocessing

sys.path.insert(1, '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python')
from vedbus import VeDbusService
from gi.repository import GLib
import dbus.mainloop.glib

SETTINGS_FILE = '/data/dbus-tank-sensor/settings.json'
SERIAL_PORT = '/dev/ttyTANK'

FLUID_TYPES = ['Fuel', 'Fresh Water', 'Waste Water', 'Live Well', 'Oil', 'Black Water']

DEFAULT_SETTINGS = {
    'tanks': [
        {'capacity': 100.0, 'fluid_type': 1, 'custom_name': 'Fresh Water'},
        {'capacity': 100.0, 'fluid_type': 0, 'custom_name': 'Fuel'},
        {'capacity': 100.0, 'fluid_type': 2, 'custom_name': 'Waste Water'},
        {'capacity': 100.0, 'fluid_type': 5, 'custom_name': 'Black Water'},
    ]
}

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
                while len(saved.get('tanks', [])) < 4:
                    idx = len(saved['tanks'])
                    saved['tanks'].append(DEFAULT_SETTINGS['tanks'][idx].copy())
                return saved
    except Exception as e:
        print(f'Error loading settings: {e}')
    return json.loads(json.dumps(DEFAULT_SETTINGS))

def save_settings(settings):
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f'Error saving settings: {e}')


def tank_process(tank_id, level_queue):
    """Run a single tank service in its own process"""
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    settings = load_settings()
    tank_settings = settings['tanks'][tank_id]
    is_active = False
    service = None
    
    def create_service():
        nonlocal service
        service_name = f'com.victronenergy.tank.tank{tank_id}'
        service = VeDbusService(service_name, register=False)
        
        service.add_path('/Mgmt/ProcessName', 'tank_service')
        service.add_path('/Mgmt/ProcessVersion', '1.0')
        service.add_path('/Mgmt/Connection', f'Serial {SERIAL_PORT}')
        service.add_path('/DeviceInstance', 20 + tank_id)
        service.add_path('/ProductId', 0)
        service.add_path('/ProductName', f'Tank {tank_id}')
        service.add_path('/FirmwareVersion', '1.0')
        service.add_path('/Connected', 1)
        
        def on_fluid_type_changed(path, value):
            try:
                val = int(float(str(value)))
                if 0 <= val <= 5:
                    tank_settings['fluid_type'] = val
                    settings['tanks'][tank_id] = tank_settings
                    save_settings(settings)
                    print(f'Tank {tank_id} fluid type changed to: {FLUID_TYPES[val]}')
                    return True
            except:
                pass
            return False
        
        def on_capacity_changed(path, value):
            try:
                val = float(str(value))
                if val > 0:
                    tank_settings['capacity'] = val
                    settings['tanks'][tank_id] = tank_settings
                    save_settings(settings)
                    print(f'Tank {tank_id} capacity changed to: {val}L')
                    return True
            except:
                pass
            return False
        
        def on_custom_name_changed(path, value):
            tank_settings['custom_name'] = str(value)
            settings['tanks'][tank_id] = tank_settings
            save_settings(settings)
            print(f'Tank {tank_id} name changed to: {value}')
            return True
        
        service.add_path('/FluidType', tank_settings['fluid_type'], writeable=True, onchangecallback=on_fluid_type_changed)
        service.add_path('/Capacity', float(tank_settings['capacity']), writeable=True, onchangecallback=on_capacity_changed)
        service.add_path('/Level', 0)
        service.add_path('/Remaining', 0)
        service.add_path('/Status', 0)
        service.add_path('/CustomName', tank_settings['custom_name'], writeable=True, onchangecallback=on_custom_name_changed)
        
        service.register()
        
        fluid_name = FLUID_TYPES[tank_settings['fluid_type']] if tank_settings['fluid_type'] < len(FLUID_TYPES) else 'Unknown'
        print(f'Tank {tank_id} ACTIVE: {tank_settings["custom_name"]} ({fluid_name}), {tank_settings["capacity"]}L')
    
    def check_queue():
        nonlocal is_active, service
        try:
            while not level_queue.empty():
                msg = level_queue.get_nowait()
                
                if msg == 'OFF':
                    if is_active:
                        is_active = False
                        if service:
                            service['/Connected'] = 0
                        print(f'Tank {tank_id} OFF')
                else:
                    try:
                        level = int(msg)
                        if 0 <= level <= 100:
                            if not is_active:
                                is_active = True
                                if service is None:
                                    create_service()
                                else:
                                    service['/Connected'] = 1
                            
                            capacity = tank_settings['capacity']
                            remaining = (level / 100.0) * capacity
                            
                            service['/Level'] = level
                            service['/Remaining'] = remaining
                            service['/Status'] = 0
                            print(f'Tank {tank_id}: {level}% ({remaining:.1f}L / {capacity}L)')
                    except:
                        pass
        except:
            pass
        return True
    
    print(f'Tank {tank_id} process started, waiting for sensor data...')
    
    GLib.timeout_add(500, check_queue)
    
    mainloop = GLib.MainLoop()
    mainloop.run()


def main():
    queues = [multiprocessing.Queue() for _ in range(4)]
    
    processes = []
    for i in range(4):
        p = multiprocessing.Process(target=tank_process, args=(i, queues[i]))
        p.daemon = True
        p.start()
        processes.append(p)
        time.sleep(0.5)
    
    print('Multi-tank service started')
    print('Ground input = OFF, otherwise shows level')
    
    ser = serial.Serial(SERIAL_PORT, baudrate=9600, timeout=3)
    time.sleep(1)
    ser.reset_input_buffer()
    
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                for i in range(4):
                    prefix = f'TANK{i}:'
                    if line.startswith(prefix):
                        value = line[len(prefix):]
                        queues[i].put(value)
                        break
        except Exception as e:
            print(f'Error: {e}')
        
        time.sleep(0.1)


if __name__ == '__main__':
    main()
