
import secrets
from datetime import datetime
from time import sleep
import serial
from logger_config import setup_logger
from src.assist_scripts.test_script_assist import simulate_magnet_sensor_hall_10s
from src.script_new_firmware.protocol_v2.scripts_assist import calc_checksum_two, check_error_flags, update_fw_st_cli, verify_check_sum_im_alive
from src.script_new_firmware.script_constant import FW_PATH, FW_PATH_DEBUG

from configs.device_configs import DeviceConfigs
from integration.connect_devices import find_pcb_uart, find_ppk2

from ppk2_api.ppk2_api2 import PPK2_API

logger = setup_logger()
def script_write_new_fw(new_keys:dict=None, magnet_automatic:bool=False,fw_path:str=FW_PATH):
        
    logger.info(f'Start of Script New FW - {datetime.now()}')
    logger.info(f'Pré-Conditions Configuration')
    logger.info(f'Device Configuration')
    DeviceConfigs.device_eui = ''
    if type(new_keys) == dict:
        DeviceConfigs.network_session_key = new_keys['network_session_key']
        DeviceConfigs.application_session_key = new_keys['application_session_key']
        DeviceConfigs.device_address = new_keys['device_address'] 
    else:
        DeviceConfigs.network_session_key = secrets.token_hex(16)
        DeviceConfigs.application_session_key = secrets.token_hex(16)
        DeviceConfigs.device_address = secrets.token_hex(4)
    logger.info(f'Power Profiler PPK2 configuration')
    ppk2_port = find_ppk2()
    ppk2_test = PPK2_API(ppk2_port, timeout=3, write_timeout=3, exclusive=True)
    sleep(2)
    ppk2_test.use_ampere_meter()
    ppk2_test.toggle_DUT_power("ON")
    
    logger.info(f'Firmware Update Started')
    update_fw_st_cli(fw_path=fw_path)
    logger.info(f'Firmware Update Finished')
    # Start Testing Message
    start_test_byte1 = '02' # STX
    start_test_byte2 = '04' # Message Id
    start_test_byte3 = '11' # Tag number in the Jig
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


    logger.info(f'Start Serial Connection')
    pcb_uart_port = find_pcb_uart()
    with serial.Serial(pcb_uart_port,baudrate=115200,bytesize=8,stopbits=1) as porta:
        resp_im_alive = porta.read(11).hex()
        verify_check_sum_im_alive(resp_im_alive)              
        DeviceConfigs.device_eui = resp_im_alive[4:20]
        logger.info(f"Response - I'm alive: {resp_im_alive}")
        
        if magnet_automatic == True:
            sleep(2)
            simulate_magnet_sensor_hall_10s()
            logger.info(f"Message -  Start testing: {start_test_message}")
            sleep(2)
            porta.write(bytes.fromhex(start_test_message))
            resp_test_report = porta.read(20).hex()
            # Check the error flags are correct
            for value in check_error_flags(resp_test_report).items():
                if value[1] == 'error':
                    stop_test_byte3 = '15'
                    stop_test_byte4 = calc_checksum_two(stop_test_byte1+stop_test_byte2+stop_test_byte3)
                    stop_test_message = stop_test_byte1+stop_test_byte2+stop_test_byte3+stop_test_byte4
                    DeviceConfigs.device_address = ''
                    DeviceConfigs.network_session_key = ''
                    DeviceConfigs.application_session_key = ''
                    logger.error(f"Error - {value[0]} : {value[1]}")
                    raise Exception("Error to update firmware")
            logger.info(f'Response - Test report: {resp_test_report}')
            sleep(2)
            logger.info(f"Message -  Stop Test: {stop_test_message}")
            porta.write(bytes.fromhex(stop_test_message))
            logger.info(f'Device Address: {DeviceConfigs.device_address}')
            logger.info(f'Network Session Key: {DeviceConfigs.network_session_key}')
            logger.info(f'Application Session Key: {DeviceConfigs.application_session_key}')
            logger.info(f'DevEui: {DeviceConfigs.device_eui}')                
        else:
            value_input = input("MAGNET ON TOP OF THE PCB? [Y/N] : ").upper()               
            if value_input == 'Y':
                logger.info(f"Message -  Start testing: {start_test_message}")
                sleep(2)
                porta.write(bytes.fromhex(start_test_message))
                resp_test_report = porta.read(20).hex()
                # Check the error flags are correct
                for value in check_error_flags(resp_test_report).items():
                    if value[1] == 'error':
                        stop_test_byte3 = '15'
                        stop_test_byte4 = calc_checksum_two(stop_test_byte1+stop_test_byte2+stop_test_byte3)
                        stop_test_message = stop_test_byte1+stop_test_byte2+stop_test_byte3+stop_test_byte4
                        DeviceConfigs.device_address = ''
                        DeviceConfigs.network_session_key = ''
                        DeviceConfigs.application_session_key = ''
                        logger.info(f"Error - {value[0]} : {value[1]}")
                        raise Exception("Error to update firmware")
                logger.info(f'Response - Test report: {resp_test_report}')
                sleep(2)
                logger.info(f"Message -  Stop Test: {stop_test_message}")
                porta.write(bytes.fromhex(stop_test_message))
                logger.info(f'Device Address: {DeviceConfigs.device_address}')
                logger.info(f'Network Session Key: {DeviceConfigs.network_session_key}')
                logger.info(f'Application Session Key: {DeviceConfigs.application_session_key}')
                logger.info(f'DevEui: {DeviceConfigs.device_eui}')
            else:
                logger.info(f"PLEASE PUT THE MAGNET ON TOP OF THE PCB")
    sleep(10)
    ppk2_test.stop_measuring()
    ppk2_test.toggle_DUT_power("OFF")
    ppk2_test.ser.close()
    sleep(2)
    logger.info(f'Firmware Update Finished - {datetime.now()}')

keys = {
    'device_address': '500122f2',  
    'network_session_key': '2b7e151628aed2a6abf7158809cf4f3c',
    'application_session_key': '2b7e151628aed2a6abf7158809cf4f3c',
}
script_write_new_fw(new_keys=keys,magnet_automatic=False,fw_path=FW_PATH)


