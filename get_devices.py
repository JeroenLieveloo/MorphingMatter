import serial
import serial.tools.list_ports
import time

def identify_arduino(connection):
    # Allow time for the Arduino to reset
    connection.write(b"WHO_ARE_YOU\n")
    response = connection.readline().decode('utf-8').strip()
    return response

def connect(port):
    try:
        with serial.Serial(port, 9600, timeout=1) as ser:
            time.sleep(2)
            return ser
    except:
        return None

def get_connected_devices():
    devices = []
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Filter out devices with no description (usually shown as "n/a")
        if port.description != 'n/a':
            device_info = {
                "device_name": port.description,
                "com_port": port.device,
                "serial_number": port.serial_number
            }
            devices.append(device_info)
    
    return devices

if __name__ == '__main__':
    devices = get_connected_devices()
    if devices:
        print("Connected USB devices:")
        for device in devices:
            print(f"Device Name: {device['device_name']}, COM Port: {device['com_port']}, Serial Number: {device['serial_number']}")
    else:
        print("No USB devices found.")
