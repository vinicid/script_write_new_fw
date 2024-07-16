
import secrets
from datetime import datetime
from time import sleep
import serial
from config.device_configs import DeviceConfigs
from integration.connect_devices import find_pcb_uart, find_ppk2
from scripts_assist import calc_checksum_two, check_error_flags,verify_check_sum_im_alive
from ppk2_api.ppk2_api2 import PPK2_API


def script_write_new_fw():
    
    
    print(f'\n---------------- Start of the Script - {datetime.now()}')
    print(f'\nPré-Conditions Configuration')
    print(f'\nDevice Configuration')
    DeviceConfigs.device_eui = ''
    DeviceConfigs.network_session_key = secrets.token_hex(16)
    DeviceConfigs.application_session_key = secrets.token_hex(16)
    DeviceConfigs.device_address = secrets.token_hex(4)

    print(f'\nMessages Configuration')
    # Start Testing Message
    start_test_byte1 = '02' # STX
    start_test_byte2 = '04' # Message Id
    start_test_byte3 = '01' # Tag number in the Jig
    start_test_byte4_19 = DeviceConfigs.network_session_key # network session key
    start_test_byte20_35 = DeviceConfigs.application_session_key # application session key 
    start_test_byte36_39 = DeviceConfigs.device_address # device address
    start_test_byte40 = calc_checksum_two(start_test_byte1+start_test_byte2+start_test_byte3+start_test_byte4_19+start_test_byte20_35+start_test_byte36_39) # checksum
    start_test_message = (start_test_byte1+start_test_byte2+start_test_byte3+start_test_byte4_19+start_test_byte20_35+start_test_byte36_39+start_test_byte40) # Start testing Message

    # Stop Test Message
    stop_test_byte1 = '02' # STX
    stop_test_byte2 = '06' # Message Id
    stop_test_byte3 = '06' # Test Result (06 - Pass, 15 - Fail)
    stop_test_byte4 =  calc_checksum_two(stop_test_byte1+stop_test_byte2+stop_test_byte3) # checksum
    stop_test_message = (stop_test_byte1+stop_test_byte2+stop_test_byte3+stop_test_byte4) # Stop Test Message

    print(f'\nPower Profiler PPK2 configuration')
    ppk2_port = find_ppk2()
    ppk2_test = PPK2_API(ppk2_port, timeout=3, write_timeout=3, exclusive=True)
    ppk2_test.set_source_voltage(3000)

    print(f'\nStart Serial Connection')
    pcb_uart_port = find_pcb_uart()
    with serial.Serial(pcb_uart_port,baudrate=115200,bytesize=8,stopbits=1) as porta:
        ppk2_test.toggle_DUT_power("OFF")
        sleep(2)
        ppk2_test.toggle_DUT_power("ON")
        resp_im_alive = porta.read(11).hex()
        verify_check_sum_im_alive(resp_im_alive)              
        DeviceConfigs.device_eui = resp_im_alive[4:20]
        print(f"Response - I'm alive: {resp_im_alive}")
        value_input = input("MAGNET ON TOP OF THE PCB? [Y/N] : ").upper()
        if value_input == 'Y':
            print(f"Message -  Start testing: {start_test_message}")
            sleep(2)
            porta.write(bytes.fromhex(start_test_message))
            resp_test_report = porta.read(16).hex()
            
            # Check the error flags are correct
            for value in check_error_flags(resp_test_report).items():
                if value[1] == 'error':
                    stop_test_byte3 = '15'
                    stop_test_byte4 = calc_checksum_two(stop_test_byte1+stop_test_byte2+stop_test_byte3)
                    stop_test_message = stop_test_byte1+stop_test_byte2+stop_test_byte3+stop_test_byte4
                    DeviceConfigs.device_address = ''
                    DeviceConfigs.network_session_key = ''
                    DeviceConfigs.application_session_key = ''
                    print(f"Error - {value[0]} : {value[1]}")
        
            print(f'Response - Test report: {resp_test_report}')
            sleep(2)
            print(f"Message -  Stop Test: {stop_test_message}")
            porta.write(bytes.fromhex(stop_test_message))
            print(f'Device Address: {DeviceConfigs.device_address}')
            print(f'Network Session Key: {DeviceConfigs.network_session_key}')
            print(f'Application Session Key: {DeviceConfigs.application_session_key}')
            print(f'DevEui: {DeviceConfigs.device_eui}')
        else:
            print(f"PLEASE PUT THE MAGNET ON TOP OF THE PCB")
    sleep(20)
    print(f'\n---------------- End of the Script - {datetime.now()}')
script_write_new_fw()



