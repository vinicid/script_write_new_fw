import os
from subprocess import *
import struct
import string
# import mcu
import re
import time
from datetime import datetime

from script_constants import GENERATE_LOG, STLINK_PATH

# STLINK_PATH = "C:\\Program Files\\STMicroelectronics\\STM32Cube\\STM32CubeProgrammer\\bin\\STM32_Programmer_CLI.exe"
# LOCK_DELAY = 1
# GENERATE_LOG: bool = True

#base
# "C:\Program Files (x86)\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe" 

#con
# "C:\Program Files (x86)\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe" -c port=SWD freq=4000 mode=UR reset=HWrst

#erase
# "C:\Program Files (x86)\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe" -c port=SWD freq=4000 mode=UR reset=HWrst -e


def run_command(args):
    try:
        print(" ".join(args))
        resp = check_output(args, shell=True)
        #print(resp)
        return resp.decode()
    except Exception as error:
        print(error)
        print("Failed to execute command, is the device connected?")
        return 0

def create_temp_file(filename):
    #creates empty file
    f = open(filename,"wb+")
    f.close()

def delete_temp_file(filename):
    if os.path.exists(filename):
        os.remove(filename)
    else:
        print("The file does not exist") 

#function for splitting byte arrays
def chunked(size, source):
    for i in range(0, len(source), size):
        yield source[i:i+size]
    
class Stlink:
    
    class Reset_Strategy():
        HOTPLUG = "HOTPLUG"
        CONNECT_UNDER_RST = "UR"

    def __init__(self):
        self.interface = ""
        self.speed = 0
        self.rm = ""
        self.target_con = ""
        self.dev_eui: str = ""
        self.reset_strategy: str = self.Reset_Strategy.HOTPLUG
        
    def generate_log_str(self):
        
        time_now = str(datetime.now().time())
        time_now = time_now.replace(':','-')
        
        current_directory = os.getcwd()
        relative_directory: str = "/stlink_log/%s" % (self.dev_eui)
        final_directory: str = current_directory + relative_directory
        if not os.path.exists(final_directory):
            os.makedirs(final_directory)
        
        return_string = "--log %s/%s.txt" % (final_directory,time_now) if GENERATE_LOG == True else ""
        
        return return_string
        

        
    def set_target_con(self,target_con):
        self.target_con = target_con

    def set_stlink_path(self, stlink_path: str):
        self.stlink_path = stlink_path
        
    def verify_path_to_cube_programmer(self):
        args = [ self.stlink_path,"--help"]
        
        try:
            #print(" ".join(args))
            resp = check_output(args, shell=True)
            return True
        
        except Exception as error:
            #print(error)
            #print("Failed to execute command, is the device connected?")
            return False

    def list(self):
        return run_command([self.stlink_path,"--list st-link"])

    def get_speed(self):
        return str(self.speed)
    
    def set_reset_strategy(self,reset_strategy: str):
        self.reset_strategy = reset_strategy
        self.connect(self.mcu, self.interface, self.speed)

    def parse_header(self, header_string):
        #print(header_string)
        #breaks header into a list of strings, removing the empty strings ("")
        lst = [string for string in header_string.split("\r\n") if string != ""]
        #print(lst)
        lst.pop(0) #removes --------....
        lst.pop(0) #removes STM32CubeProgrammer vX.Y.Z
        lst.pop(0) #removes --------....
        lst.pop(0) #removes --------....
        print(lst)
        #now only values shold be left
        dic = {}
        for pair in lst:
            #remove duplicate spaces and split at :
            try:
                value = " ".join(pair.split()).split(':')
                #add values to dictionary, removing trailing or leading spaces
                dic[value[0].strip()] = value[1].strip()
                
            except:
                value = " ".join(pair.split()).split('=')
                #add values to dictionary, removing trailing or leading spaces
                dic[value[0].strip()] = value[1].strip()
                
        print(dic)
        return dic

    def connect(self, mcu, interface="SWD", speed=4000):
        self.device = ""
        self.mcu=mcu
        self.interface = interface
        self.speed = speed
        self.connect_str = " ".join(["-c", "port=%s"%interface, "sn=%s"%self.target_con ,"freq=%d"%(speed),"mode=%s" % (self.reset_strategy), "reset=SWrst"])
        return self.is_connected()
    
    def connect_fast(self):
        self.device = ""
        self.connect_str = " ".join(["-c", "port=SWD" ,"freq=4000","mode=Normal", "reset=HWrst"])
        return self.is_connected()
    
    def disconnect(self):
        pass

    def is_connected(self):
        try:
            dic = self.parse_header( run_command([self.stlink_path,self.connect_str,self.generate_log_str()]))
            self.device = dic["Device ID"]
            self.dic = dic
            if(self.device!=""):
                return True
        except Exception as e:
            print("Failed to connect to target using ST link")
            print(e)
            
        return False
    
    def get_bor_level(self):
        """ Checks if the MCU is locked and returns True if it is"""
        if("stm32wle5xx" in self.mcu.device.lower()):
            data = self.read(0x1FFF7800,4)
            
        if data == 0:
            return 0
            
        data = int.from_bytes(data, byteorder='little')
        
        bor=data&0b111000000000
        bor=bor>>9
        print("BOR level value: %0x"%bor )
        return bor

    def read(self,addr,num_bytes):
        temp_file = self.target_con + "temp_file.bin"
        output = run_command([self.stlink_path, self.connect_str,"-q", "-r","0x%04x"%addr, str(num_bytes), temp_file,self.generate_log_str()])
        if ("successfully" not in str(output)):
            print("Could not read from MCU")
            return 0
        file = open(temp_file, "rb")
        data = file.read()
        file.close()
        delete_temp_file(temp_file)
        return data
    
    def write_w8(self, addr, data):
        """writes a 8bit wide word to the target's flash or sram"""
        
        data_str = "0x%02x" % data
        print(data_str)
        output = run_command([self.stlink_path, self.connect_str,"-q -w8 0x%08x"%addr, data_str,self.generate_log_str()])
        return output
    
    def read_register(self, addr):
        """Reads a 32bit wide word from the target's flash or sram"""
        temp_file = self.target_con + "temp_file.bin"
        num_bytes = 4
        output = run_command([self.stlink_path, self.connect_str,"-q", "-r32","0x%04x"%addr, str(num_bytes), temp_file,self.generate_log_str()])
        print(str(output))
        if ("successfully" not in str(output)):
            print("Could not read from MCU")
            return 0
        file = open(temp_file, "rb")
        data = file.read()
        file.close()
        delete_temp_file(temp_file)
        return data
    
    def write_register(self, addr, data):
        """writes a 32bit wide word to the target's flash or sram"""
        
        #the stm32cube ide cli program uses 32bit writes, so padding is needed
        print(data)
        if((len(data)%4)!=0):
            #pad data to be multiple of 4 bytes
            data += b'\x00'*(4-(len(data)%4)) 
            print(data)
        chunks = list(chunked(4, data)) 
        print(chunks)
        #converts bytearray to a string of bytes preceded by 0x
        data_str = " ".join(["0x%08x"%int.from_bytes(i, byteorder='big', signed=False) for i in chunks])
        print(data_str)
        output = run_command([self.stlink_path, self.connect_str,"-q -w32 0x%08x"%addr, data_str,self.generate_log_str()])
        return output


    def erase(self):
        start = 0
        end = (self.mcu.flash_size/self.mcu.sector_size) -1
        output = run_command([self.stlink_path, self.connect_str,"-e [%d %d]"%(start, int(end)),self.generate_log_str()])
        return output
    
    def program_file(self,img_path,addr):
        output = run_command([self.stlink_path, self.connect_str,"-q --write", img_path, "0x%04x"%addr,self.generate_log_str()])
        
        if 'File download complete' in output:
            return 'success'
        
        return output
    
    def program_bytes(self,data,addr):
        
        #the stm32cube ide cli program uses 32bit writes, so padding is needed
        print(data)
        if((len(data)%4)!=0):
            #pad data to be multiple of 4 bytes
            data += b'\x00'*(4-(len(data)%4)) 
            print(data)
        chunks = list(chunked(4, data)) 
        print(chunks)
        #converts bytearray to a string of bytes preceded by 0x
        data_str = " ".join(["0x%08x"%int.from_bytes(i, byteorder='little', signed=False) for i in chunks])
        print(data_str)
        output = run_command([STLINK_PATH, self.connect_str,"-q -w32 0x%08x"%addr, data_str,self.generate_log_str()])
        return output
        
        '''
        filename = "eeprom.bin"
        with open(filename, 'wb') as f:
            f.write(data)
            
        output = run_command([self.stlink_path, self.connect_str,"-q --write", filename, "0x%04x"%addr])
        '''
    def hw_get_unique_id(self):
        if(self.is_connected()!=True):
            print("The device does not seem to be connected, can not read device id")
            return 0
        id1 = self.read(self.mcu.id_address[0],4)
        id2 = self.read(self.mcu.id_address[1],4)

        self.dev_eui = [id2[3], id2[2], id2[1], id2[0], id1[3], id1[2] , id1[1] , id1[0] ]
        self.dev_eui = ''.join(format(x,'02x') for x in bytearray(self.dev_eui))
        print(self.dev_eui)
        return self.dev_eui
    
    def set_bor_level(self,bor_level):
        output = run_command([self.stlink_path, self.connect_str,"-q --optionbytes bor_lev=%d"%(bor_level),self.generate_log_str()])
        return output

    def reset_mcu(self,halt: bool = False, restart: bool = True):
        run_command([self.stlink_path, self.connect_str,"-q -hardRst",self.generate_log_str()])
        
        if halt:
            self.halt()
            
        if restart:
            self.restart()

    def restart(self):
        output = run_command([self.stlink_path, self.connect_str,"-q -rst",self.generate_log_str()])
        return output

    def halt(self):
        output = run_command([self.stlink_path, self.connect_str,"-q -halt",self.generate_log_str()])
        return output
    
    def run(self):
        output = run_command([self.stlink_path, self.connect_str,"-q -run",self.generate_log_str()])
        return output
    
    def lock_mcu(self):
        """ MCU protecting procedure """
        output = run_command([self.stlink_path, self.connect_str,"-q --optionbytes rdp=0xBB -ob BOR_LEV=0x03",self.generate_log_str()])
        return output
#===============================================================================
#         self.halt()
#         #no need to unprotect if the MCU is already protected
#         if(self.is_mcu_locked()==True):
#             print("MCU already locked!")
#             self.run()
#             return True
# 
#         #unlocks writing to the option bytes registers
#         self.unlock_option_bytes_register()
#         
#         time.sleep(LOCK_DELAY)
# 
#         optr_bytes = int.from_bytes(self.read(0x58004020,4), byteorder='little')
#         optr_bytes = optr_bytes | (0xBB << 0)#Apply RDP protection
#         optr_bytes = optr_bytes | (0x03 << 9)#Set BOR level 3
#         
#         self.write_register(0x58004020, optr_bytes.to_bytes(4,'big'))
#         
#         time.sleep(LOCK_DELAY)
#         
#         self.write_register(0x58004014, (0x00020000).to_bytes(4,'big')) # Set the Options Start bit OPTSTRT in FLASH_CR
#         self.write_register(0x58004014, (0x08020000).to_bytes(4,'big')) # Set the Options Start bit OBL_LAUNCH in FLASH_CR
#         
#         time.sleep(LOCK_DELAY)
#         self.reset_mcu()
#         
#         #verifies if programming was succesfull
#         if(self.is_mcu_locked()==True):
#             return True
#         
#         return False
#===============================================================================
    
    def unlock_mcu(self):
        output = run_command([self.stlink_path, self.connect_str,"--readunprotect",self.generate_log_str()])
        return output

#===============================================================================
#         """ MCU unlcoking procedure """
#         self.halt()
#         #Returns if the MCU is already unprotected
#         if(self.is_mcu_locked()==False):
#             print("MCU already unlocked!")
#             self.run()
#             return True
#         
#         self.unlock_option_bytes_register()
#         time.sleep(LOCK_DELAY)
#         
#         optr_bytes = int.from_bytes(self.read(0x58004020,4), byteorder='little')
#         optr_bytes = optr_bytes & (0xffffff00)#Clear RDP Byte
#         optr_bytes = optr_bytes | (0xAA << 0)#Remove RDP protection
#         
#         self.write_register(0x58004020, optr_bytes.to_bytes(4,'big'))
#         
#         time.sleep(LOCK_DELAY)
#         
#         self.write_register(0x58004014, (0x00020000).to_bytes(4,'big')) # Set the Options Start bit OPTSTRT in FLASH_CR
#         self.write_register(0x58004014, (0x08020000).to_bytes(4,'big')) # Set the Options Start bit OBL_LAUNCH in FLASH_CR
#         
#         time.sleep(LOCK_DELAY)
# 
#         self.reset_mcu()
#         
#         if(self.is_mcu_locked()==False):
#             return True
#         return False
#===============================================================================
    
    def unlock_option_bytes_register(self):
        """Unlocks first the flash and then the option bytes
        
        This procedure is done according to the reference manual
        of the selecteds architectures.
        """
        
        self.write_register(0x58004008, (0x45670123).to_bytes(4,'big')) # Unlock FLASH_CR with KEY1 and KEY2
        self.write_register(0x58004008, (0xCDEF89AB).to_bytes(4,'big'))
        self.write_register(0x5800400C, (0x08192A3B).to_bytes(4,'big')) # Unlock option byte block with OPTKEY1 and OPTKEY2
        self.write_register(0x5800400C, (0x4C5D6E7F).to_bytes(4,'big'))
        self.write_register(0x58004010, (0x0000C3FB).to_bytes(4,'big')) # Clear all error bits in the FLASH_SR


    def is_mcu_locked(self):
        if(self.is_connected()!=True):
            print("The device does not seem to be connected, can not read device id")
            return 0
        output = run_command([self.stlink_path, self.connect_str,"-q --optionbytes displ",self.generate_log_str()])
        lst = output.split("\r\n")
        for line in lst:
            if re.search("RDP          :", line):
                print(line)
                #only get first 25 chars, then split at the : and get only the hex value
                rdp_value = line[0:25].split(": ")[1]
        print(rdp_value)
        if("0xaa" in rdp_value.lower()):
            print("Mcu is unlocked (%s)"%rdp_value)
            return False
        
        print("Mcu is locked (%s)"%rdp_value)
        return True

if __name__ == '__main__':

    pass

    # teste = Stlink()
    # teste.set_stlink_path(STLINK_PATH)
    # teste.connect_fast()
    # print(teste.program_file("C:\\Firmwares\\tagvis\\fw\\src\\Projects\\LoRaWAN_End_Node\\STM32CubeIDE\Debug\\STM32CubeIDE.bin",0x08000000))
    # if teste.is_connected() == True:
    #     teste.disconnect()
    
   
    # print(teste.read(0x08000000, 5))
    # teste.connect(micro)
    # print(teste.hw_get_unique_id())
    
    #print(teste.hw_get_unique_id())
    #teste.unlock_mcu()
    #print(teste.is_mcu_locked())
    
    #print(teste.set_bor_level(0))
    
    #print(teste.lock_mcu())
    #print(teste.unlock_mcu())
  
    
    #teste.get_bor_level()
    
    #data = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x08, 0x01, 0x02,0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
    #teste.program_bytes(data, 0x0803F7FF)

    
    #print(teste.program_file("C:\\Users\\Tiago\\GIT\\fotocelula-iot\\fw\\src\\Projects\\foto_wle5jc\\STM32CubeIDE\\Debug\\foto_wle5jc.bin1",micro.flash_address))
    
    #teste.lock_mcu()
    #teste.is_mcu_locked()
    #print(teste.read(0x08000000, 5))
    #teste.program("./BLE_p2pServer_reference.hex", micro.flash_address)
    #teste.reset_mcu()
    #teste.unlock_mcu()
    #data = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x08, 0x01, 0x02])
    #teste.program_bytes(data, 0x08000000)
   
    #teste.is_mcu_locked()
    #print(teste.read(0x20000804, 14))
    #print(teste.is_connected())

    # teste.connect(mcu)
    # teste.jlink_prog.reset()
    # if(not teste.is_mcu_locked()):
    #     print("Device EUI: %s "%(teste.hw_get_unique_id()))
        
    # teste.lock_mcu()
    # teste.is_mcu_locked()
    # teste.unlock_mcu()
    # teste.erase()
    # teste.is_mcu_locked()