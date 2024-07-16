import os
from ppk2_api.ppk2_api2 import PPK2_API


@staticmethod
def pcb_uart_list_devices():
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    if os.name == 'nt':
        devices = [port.device for port in ports if port.hwid.startswith("USB VID:PID=1A86:7523 SER= LOCATION=1-3.4.4")]
    else:
        devices = [port.device for port in ports if port.product == 'PPK2']
    return devices

@staticmethod
def ppk2_list_devices():
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        if os.name == 'nt':
            devices = [port.device for port in ports if port.description.startswith("nRF Connect USB CDC ACM")]
        else:
            devices = [port.device for port in ports if port.product == 'PPK2']
        return devices

def find_pcb_uart() -> any:
    uart_connected = pcb_uart_list_devices()
    if(len(uart_connected) == 1):
        uart_port = uart_connected[0]
        print(f'Found PPK2 at {uart_port}')
    else:
        print(f'Too many connected PPK2\'s: {uart_connected}')
        exit()
    return uart_port

def find_ppk2() -> any:
    ppk2s_connected = ppk2_list_devices()
    if(len(ppk2s_connected) == 1):
        ppk2_port = ppk2s_connected[0]
        print(f'Found PPK2 at {ppk2_port}')
    else:
        print(f'Too many connected PPK2\'s: {ppk2s_connected}')
        exit()
    return ppk2_port