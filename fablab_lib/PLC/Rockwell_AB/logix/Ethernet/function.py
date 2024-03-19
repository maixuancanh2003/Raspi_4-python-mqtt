"""
This file contains functions and classes related to the Rockwell AB PLC and Ethernet communication.

Functions:
- is_ethernet_connected: Checks if the Ethernet connection to a specified IP address is active.
- waiting_for_connection: Waits for the Ethernet connection to be active.
- get_variables_from_equation: Extracts unique variables from an equation.
- convert_logic_equation: Converts a logic equation into a boolean result.
- DictAsAttributes: A class that converts a dictionary to attributes.
- PLC: A class representing the Rockwell AB PLC.

Library: pylogix
Installation: pip install pylogix
"""
import subprocess
import logging
import time
import threading
from . import pylogix

lock = threading.Lock()

# Application logger
logger = logging.getLogger("PLC_Rockwell_AB")
logger.setLevel(logging.DEBUG)
_log_handle = logging.StreamHandler()
_log_handle.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s | %(message)s'))
logger.addHandler(_log_handle)


def is_ethernet_connected(host: str, is_pc: bool = False) -> bool:
    """
    Checks if the Ethernet connection to the specified IP address is active.

    Args:
        host (str): The IP address to ping.
        is_pc (bool, optional): Specifies whether the IP address belongs to a Laptop. Defaults to False for Raspberry Pi connection.

    Returns:
        bool: True if the Ethernet connection is active, False otherwise.
    """
    try:
        if is_pc:
            ping_command = ["ping", "-n", "1", host]
        else:
            ping_command = ["ping", "-c", "1", host]
        ping_process = subprocess.Popen(ping_command, 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE
                                        )

        return_code = ping_process.wait()
        if return_code == 0:
            logger.info(f"Ethernet connection to {host} is active.")
            return True
        else:
            logger.info(f"Ethernet connection to {host} is not active.")  
            return False
        
    except subprocess.CalledProcessError as e:
        # Handle subprocess errors if needed
        logger.error(f"Error running ping command: {e}")
        return False


def waiting_for_connection(host: str, is_pc: bool = False): 
    """
    Waits for the Ethernet connection to be active in the first time.

    Args:
        host (str): The IP address to ping.
        is_pc (bool, optional): Specifies whether the IP address belongs to a Laptop. Defaults to False for Raspberry Pi connection.

    Returns:
        None
    """
    while True:
        if is_ethernet_connected(host, is_pc):
            return


def get_variables_from_equation(equation):
    """
    Extracts all unique variables from the given equation and returns them in alphabetical order.

    Args:
        equation (str): The equation from which variables need to be extracted.

    Returns:
        list: A sorted list of unique variables found in the equation.
    """
    # Extract all unique variables from the equation
    variables = set(char for char in equation if char.isalpha())
    # Sort the variables in alphabetical order
    sorted_variables = sorted(variables)
    return sorted_variables


def convert_logic_equation(bits, equation):
    """
    Converts a logic equation into a boolean result based on the given bits.

    Args:
        bits (list): A list of bits representing the values of variables in the equation.
        equation (str): The logic equation to be evaluated.
        Note: The equation must be in the form of a Python logic equation. ".", "|", "/" are the logical operators 
            for "and", "or", "not" respectively. The variable names must be in lower case.

    Returns:
        bool: The boolean result of the evaluated logic equation.

    Examples:
        >>> convert_logic_equation([True, False, True, True, False], '/a|(b.c)|d')
        True
    """
    lsVariables = get_variables_from_equation(equation)
    # Replace variable names with corresponding bits
    for chr_ in lsVariables:
        if chr_.isalpha() and chr_.lower() in 'abcdefghijklmnopqrstuvwxyz':
            equation = equation.replace(chr_, str(int(bits[ord(chr_) - 97])))

    # Replace the logical operators with Python syntax
    equation = equation.replace('.', ' and ')
    equation = equation.replace('|', ' or ')
    equation = equation.replace('/', ' not ')
    # Remove all extra spaces from the equation
    equation = ' '.join(equation.split())

    # Evaluate the expression using eval
    result = bool(eval(equation))
    logger.info(f"Logic equation: {equation} = {result}")
    return result


class DictAsAttributes:
    """A class that converts a dictionary to attributes.
    
    Args:
        list_key (list): A list of keys of the dictionary.
        
    Returns:
        None
    
    Note: All attributes are lowercase and set in alphabetical order (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p,...).
    Example:
        >>> list_key = ['M1', 'M0', 'Y4', 'M170', 'M3', 'TS4', 'M799']
        >>> dict_status_addr = DictAsAttributes(list_key)
        >>> dict_status_addr.m1
        'a'
        >>> dict_status_addr.m0
        'b'
    """
    def __init__(self, list_key):
        list_value = [chr(97+i) for i in range(len(list_key))]
        dictionary = dict(zip(list_key, list_value))
        self.__dict__['_data'] = dictionary

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        else:
            raise AttributeError(f"'DictAsAttributes' object has no attribute '{name}'")


class PLC:
    def __init__(self, 
            host: str, 
            port: int = 44818, 
            slot: int = 0,
            is_Micro800: bool = False,
            nameStation: str=None,
            is_pc=False
        ) -> None:
        """
        Initializes the PLC Rockwell AB.
        
        Args:
            host (str): The IP address of the PLC.
            port (int, optional): The port number of the PLC. Defaults to 44818.
            slot (int, optional): The slot number of the PLC. Defaults to 0.
            is_Micro800 (bool, optional): Specifies whether the PLC is Micro800. Defaults to False.
            nameStation (str, optional): The name of the PLC station. Defaults to None.
            is_pc (bool, optional): Specifies whether the IP address belongs to a Laptop. Defaults to False for Raspberry Pi connection.
            
        Returns:
            None
        """
        self.host = host
        self.port = port
        self.slot = slot
        self.is_Micro800 = is_Micro800
        self.nameStation = nameStation
        self.is_pc = is_pc

        if self.nameStation is not None:
            logger.name = f'PLC_Rockwell_AB - {self.nameStation}'

        waiting_for_connection(self.host, self.is_pc)
        # Connect to the PLC
        self.plc = pylogix.PLC(ip_address=self.host, slot=self.slot, Micro800=self.is_Micro800, port=self.port)

    
    def readData(self, varTag: str, varType=None, varSize: int = 1, _DEBUG: bool = False):
        """
        Reads data from the PLC Rockwell AB.
        
        Args:
            varTag (str): The variable tag to be read.
            varType (int, optional): The data type of the variable. Defaults to None.
            varSize (int, optional): The size of the variable. Defaults to 1.
            _DEBUG (bool, optional): Specifies whether to print debug messages. Defaults to False.
            
        Returns:
            tuple: A tuple of variable tag and value.
        """
        with lock:
            read_result = self.plc.Read(tag=varTag, count=varSize, datatype=varType)
        
        tagName = read_result.TagName
        tagValue = read_result.Value

        if _DEBUG:
            logger.info(f"Read data from PLC: {tagName}, {tagValue}")
        return tagName, tagValue
    

    def writeData(self, varTag: str, varValue, varType=None, _DEBUG: bool = False):
        """
        Writes data to the PLC Rockwell AB.
        
        Args:
            varTag (str): The variable tag to be written.
            varValue (any): The value to be written.
            varType (int, optional): The data type of the variable. Defaults to None.
            _DEBUG (bool, optional): Specifies whether to print debug messages. Defaults to False.
            
        Returns:
            None
        """
        with lock:
            self.plc.Write(tag=varTag, value=varValue, datatype=varType)
        
        if _DEBUG:
            logger.info(f"Write data to PLC: {varTag}, {varValue}")


    def read_multiple_incoherent_bits(self, ls_varTag: list, _DEBUG: bool = False) -> list:
        """
        Reads multiple bits from the PLC Rockwell AB.
        
        Args:
            ls_varTag (list): A list of variable tags to be read.
            _DEBUG (bool, optional): Specifies whether to print debug messages. Defaults to False.
            
        Returns:
            list: A list of boolean values corresponding to the values of the variables.
        """
        varValue = []
        for varTag in ls_varTag:
            _, read_result = self.readData(varTag, varType=193)
            varValue.append(bool(read_result))

        if _DEBUG:
            logger.info(f"Read data from PLC: \n{ls_varTag} \n{varValue}")
        return varValue


    def checkLogicBits(self, bits: list, equation: str) -> bool:
        """
        Checks the logic bits.
        
        Args:
            bits (list): A list of bits representing the values of variables in the equation.
            equation (str): The logic equation to be evaluated.
            Note: The equation must be in the form of a Python logic equation. ".", "|", "/" are the logical operators 
            for "and", "or", "not" respectively. The variable names must be in lower case.
            
        Returns:
            bool: The boolean result of the evaluated logic equation.
        
        Examples:
            >>> checkLogicBits([True, False, True, True, False], '/a|(b.c)|d')
            True
        """
        return convert_logic_equation(bits, equation)


    def reconnect(self, refVarTag: str) -> None:
        """
        Reconnects to the PLC Rockwell AB.
        
        Args:
            refVarTag (str): The reference variable tag to read cyclically to check the connection.
        """
        count = 0
        case = 0
        while True:
            print(case)
            if case == 1:
                # connect
                logger.info(f"Connecting to PLC...")
                try:
                    self.plc.conn.connect()
                    logger.info(f"Connected to PLC.")
                    case = 2
                except Exception as e:
                    logger.error(f"Error connecting to PLC: {e}")
                    case = 1
                    time.sleep(5)
            elif case == 2:
                # running => read cyclic the service level if it fails disconnect and unsubscribe => wait 5s => connect
                try:
                    _, service_level = self.readData(refVarTag)

                    logger.info(f"Service level: {service_level}")
                    if service_level:
                        count += 1
                        case = 2
                        time.sleep(0.2)
                        if count == 5:
                            count = 0
                            logger.info(f"Connected to PLC {self.host}.")
                            return
                    else:
                        case = 3
                        time.sleep(5)
                except Exception as e:
                    logger.error(f"Error during operation: {e}")
                    case = 3
            elif case == 3:
                # disconnect
                logger.info(f"Disconnecting from PLC...")
                try:
                    self.plc.Close()
                except Exception as e:
                    logger.error(f"Error disconnecting from PLC: {e}")
                case = 0
            else:
                # wait
                case = 1
                time.sleep(5)


    def disconnect(self) -> None:
        """
        Disconnects from the PLC Rockwell AB.
        """
        self.plc.Close()
        logger.info(f"Disconnected from PLC {self.host}.")