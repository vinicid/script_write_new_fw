
from stlink import Stlink
from script_constants import ADDRESS_STLINK, FW_PATH, STLINK_PATH


def calc_checksum_two(value:str)-> str:
    """Calculate checksum of string value passed as argument.

    Args:
        value (str): string value to calculate checksum.

    Returns:
        str: calculated checksum string value
    """        
    return hex(((sum(int(value[i:i+2],16) for i in range(0, len(value), 2))%0x100)^0xFF)+1)[2:]

def verify_check_sum_im_alive(text_value:str):
    """Assertion function to verify the sum of bytes message i'm alive.
    """            
    assert text_value[-2:] == calc_checksum_two(text_value[:2]+text_value[2:4]+text_value[4:20])

def check_error_flags(hex_value:bytes) -> dict:
    """Check the error flags.

    Args:
        hex_value (bytes): hex value to check.

    Returns:
        dict: Returns the error flags dictionary.
    """    
    bin_error_flags = bin(int(hex_value[22:24],16))[2:]
    dict_error_flag = {
            'GNSS UART': 'error' if int(bin_error_flags[-1]) else 'no error', 
            'GNSS PPS Level':'error' if int(bin_error_flags[-2]) else 'no error', 
            'Accel I2C': 'error' if int(bin_error_flags[-3]) else 'no error', 
            'Accel INT': 'error' if int(bin_error_flags[-4]) else 'no error', 
            'Accel Valid': 'error' if int(bin_error_flags[-5]) else 'no error', 
            'RTC': 'error' if int(bin_error_flags[-6]) else 'no error', 
            'HALL': 'error' if int(bin_error_flags[-7]) else 'no error', 
            # 'Radio (P2P)': 'error' if int(bin_error_flags[-8]) else 'no error', 
    }
    return dict_error_flag

def replace_str_index(text,index,replacement=' '):
    """Replace string index.

    Args:
        text (_type_): _description_
        index (_type_): _description_
        replacement (str, optional): _description_. Defaults to ' '.

    Returns:
        _type_: _description_
    """    
    return f'{text[:index]}{replacement}{text[index+1:]}'

def update_fw(fw_path:str=FW_PATH,address:bytes=ADDRESS_STLINK):
    """Update the fw according to the new version.

    Args:
        fw_path (str, optional): Firmware path to update in the device. Defaults to FW_PATH.
        address (bytes, optional): Address initial to update. Defaults to ADDRESS_STLINK.
    """    
    stlink = Stlink()
    stlink.set_stlink_path(STLINK_PATH)
    stlink.connect_fast()
    print(stlink.program_file(fw_path,address))
    if stlink.is_connected() == True:
        stlink.disconnect()




