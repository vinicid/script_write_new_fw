class DeviceConfigs:
    """Class for device configs, getters, setters and attributes of the class.
    """    

    def __init__(
            self,
            device_eui:str,
            device_address:str,
            application_id:str,
            network_session_key:str,
            application_session_key:str,
        ):
        """Args for the class device configs class.

            device_eui (str): current device eui value.
            device_address (str): current device address value.
            application_id (str): current application id value.
            network_session_key (str): current network session key value.
            application_session_key (str): current application session key value.
        """        
        self.device_eui = device_eui
        self.application_id = application_id
        self.device_address = device_address
        self.network_session_key = network_session_key
        self.application_session_key = application_session_key
        
    @property
    def device_eui(self):
        return self.device_eui
    
    @device_eui.setter
    def device_eui(self,value):
        self.device_eui = value

    @property
    def device_address(self):
        return self.device_address

    @device_address.setter
    def device_address(self, value):
        self.device_address = value

    @property
    def application_id(self):
        return self.application_id
    
    @application_id.setter
    def application_id(self,value):
        self.port = value

    @property
    def network_session_key(self):
        return self.network_session_key

    @network_session_key.setter
    def network_session_key(self, value):
        self.network_session_key = value
    
    @property
    def application_session_key(self):
        return self.application_session_key
    
    @application_session_key.setter
    def application_session_key(self, value):
        self.application_session_key = value