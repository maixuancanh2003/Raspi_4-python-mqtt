"""
This file contains the implementation of various functions and classes related to the Siemens S7-200-SMART PLC over Ethernet communication.

Functions:
- is_ethernet_connected: Checks if the Ethernet connection to the specified IP address is active.
- waiting_for_connection: Waits for the Ethernet connection to be active in the first time.
- get_variables_from_equation: Extracts all unique variables from the given equation and returns them in alphabetical order.
- convert_logic_equation: Converts a logic equation into a boolean result based on the given bits.
- readData: Reads data from the PLC S7-200-SMART.
- writeData: Writes data to the PLC S7-200-SMART.

Classes:
- DictAsAttributes: A class that converts a dictionary to attributes.
- PLC: Represents a Siemens S7-200-SMART PLC and provides methods for connecting to the PLC and reading/writing data.

Note: This file requires the snap7 library for communication with the PLC.
Libary: python-snap7
Install: pip install python-snap7   or    pip3 install python-snap7
"""
from fablab_lib.PLC.Siemens.snap7.Ethernet import snap7
from fablab_lib.PLC.Siemens.snap7.Ethernet.snap7.util import *
import subprocess
import logging
import time
import threading

lock = threading.Lock() # Create a lock to prevent multiple threads from accessing the same PLC at the same time

# Application logger
logger = logging.getLogger("PLC_S7-200")
logger.setLevel(logging.DEBUG)
_log_handle = logging.StreamHandler()
_log_handle.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s | %(message)s'))
logger.addHandler(_log_handle)


class DT:
    """Data types of the PLC S7-200-SMART."""
    Bit = 1
    Byte = 2
    Char = 3
    Word = 4
    Int = 5
    DWord = 6
    DInt = 7
    Real = 8
    Counter = 0x1C
    Timer = 0x1D


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
            rack: int = 0, # rack 0 for S7-200
            slot: int = 1, # slot 1 for S7-200
            localtsap: int = 0x1000,
            remotetsap: int = 0x301,
            nameStation: str = None,
            is_pc=False
        ) -> None:
        """
        Represents a Siemens S7-200-SMART PLC and provides methods for connecting to the PLC and reading/writing data.
        
        Args:
            host (str): The IP address of the PLC.
            rack (int, optional): The rack number of the PLC. Defaults to 0.
            slot (int, optional): The slot number of the PLC. Defaults to 1.
            localtsap (int, optional): The local TSAP of the PLC. Defaults to 0x1000.
            remotetsap (int, optional): The remote TSAP of the PLC. Defaults to 0x301.
            nameStation (str, optional): The name of the PLC station. Defaults to None.
            is_pc (bool, optional): Specifies whether the IP address belongs to a Laptop. Defaults to False for Raspberry Pi connection.
        """
        self.host = host
        self.rack = rack
        self.slot = slot
        self.localtsap = localtsap
        self.remotetsap = remotetsap
        self.nameStation = nameStation
        self.is_pc = is_pc

        if self.nameStation is not None:
            logger.name = f'PLC_S7_200_SMART - {self.nameStation}'

        waiting_for_connection(self.host, self.is_pc)


    def connect(self) -> None:
        """
        Connects to the PLC S7-200-SMART.
        """
        self.plc = snap7.client.Client()
        self.plc.set_connection_params(self.host, self.localtsap, self.remotetsap)
        self.plc.connect(self.host, self.rack, self.slot)

        if (self.plc.get_connected()):
            logger.info(f"Connected to PLC {self.host}.")
        else:
            logger.error(f"Error connecting to PLC {self.host}.")

    
    def readData(self, varAddr: str, returnByte: bool=False, _DEBUG: bool=False):
        """
        Reads data from the PLC S7-200-SMART.
        
        Args:
            varAddr (str): The address of the variable.
            returnByte (bool, optional): Whether to return the whole byte or not. Defaults to False.
            
        Returns:
            varAddr (str): The address of the variable.
            varValue (any): The value of the variable.
            
        Note: The address of the variable must be in the form: 
        \'Vx0', 'Vx13', 'VB0', 'VW0', 'VD0' : memory
        \'Y0', 'Y13'   : output
        \'X0', 'X13'   : input
        \'CT0', 'CT10' : counter
        \'TM0', 'TM10' : timer
        """
        area = Areas.MK
        length = 1
        out = None
        bit = 0
        start = 0
        
        if len(varAddr) == 2:
            varAddr = varAddr[0] + '0' + varAddr[1]
        # Convert the address 'X0', 'Y0' to the form 'iX0', 'qX0'
        if varAddr[0].lower() == 'x':
            # varAddr = 'ix' + varAddr[1:]
            varAddr = f'ix{varAddr[1:len(varAddr)-1]}.{varAddr[-1]}' 
        elif varAddr[0].lower() == 'y':
            # varAddr = 'qx' + varAddr[1:]
            varAddr = f'qx{varAddr[1:len(varAddr)-1]}.{varAddr[-1]}'
        
        # Determine the area of the variable
        if varAddr[0].lower() == 'v':
            area = Areas.MK
        elif varAddr[0].lower() == 'q':
            area = Areas.PA
        elif varAddr[0].lower() == 'i':
            area = Areas.PE
        elif varAddr[0].lower() == 'c':
            area = Areas.CT
            length = 2
            out = DT.Counter
        elif varAddr[0].lower() == 't':
            area = Areas.TM
            length = 2
            out = DT.Timer

        # Determine the data type of the variable
        if varAddr[1].lower() == 'x':  # bit
            length = 1
            out = DT.Bit
        elif varAddr[1].lower() == 'b':  # byte
            length = 1
            out = DT.Byte
        elif varAddr[1].lower() == 'w':  # word
            length = 2
            out = DT.Word
        elif varAddr[1].lower() == 'd':  # dword
            length = 4
            out = DT.DWord
        
        # Check if the data type is valid
        if out is None:
            logger.error(f"Invalid data type with address {varAddr}.")
            return varAddr, None

        # Split the address to get the bit address
        if DT.Bit == out:
            bit = int(varAddr.split('.')[1])
            start = int(varAddr.split('.')[0][2:])
            if bit > 7:
                logger.error(f"Bit address must be less than 8 with address {varAddr}.")
                return varAddr, None
        else:
            # Split the address to get the start address
            start = int(varAddr[2:])

        # Read data from the PLC
        with lock:
            if varAddr[0].lower() == 'v':
                mbyte = self.plc.db_read(1, start, length)
            else:
                mbyte = self.plc.read_area(area, 0, start, length)

        # Convert the data to the corresponding data type
        if returnByte:
            varValue = mbyte
        elif DT.Bit == out:
            varValue = int(get_bool(mbyte, 0, bit))
        elif DT.Byte == out:
            varValue = get_byte(mbyte, 0)
        elif DT.Word == out:
            varValue = get_uint(mbyte, 0)
        elif DT.DWord == out:
            varValue = get_udint(mbyte, 0)
        elif DT.Counter == out:
            varValue = get_uint(mbyte, 0)
        elif DT.Timer == out:
            varValue = get_udint(mbyte, 0)

        if _DEBUG:
            logger.info(f"Read data from PLC: {varAddr}, {varValue}")

        return varAddr, varValue


    def writeData(self, varAddr: str, varValue, _DEBUG: bool=False):
        """
        Writes data to the PLC S7-200-SMART.

        Args:
            varAddr (str): The address of the variable.
            varValue (any): The value of the variable.

        Returns:
            None
        """
        area = Areas.MK
        out = None
        bit = 0
        start = 0

        if len(varAddr) == 2:
            varAddr = varAddr[0] + '0' + varAddr[1]
        # Convert the address 'X0', 'Y0' to the form 'iX0', 'qX0'
        if varAddr[0].lower() == 'x':
            varAddr = 'ix' + varAddr[1:]
        elif varAddr[0].lower() == 'y':
            varAddr = 'qx' + varAddr[1:]
        
        # Determine the area of the variable
        if varAddr[0].lower() == 'v':
            area = Areas.MK
        elif varAddr[0].lower() == 'q':
            area = Areas.PA
        elif varAddr[0].lower() == 'i':
            area = Areas.PE
        elif varAddr[0].lower() == 'c':
            area = Areas.CT
            out = DT.Counter
        elif varAddr[0].lower() == 't':
            area = Areas.TM
            out = DT.Timer

        # Determine the data type of the variable
        if varAddr[1].lower() == 'x':  # bit
            out = DT.Bit
        elif varAddr[1].lower() == 'b':  # byte
            out = DT.Byte
        elif varAddr[1].lower() == 'w':  # word
            out = DT.Word
        elif varAddr[1].lower() == 'd':  # dword
            out = DT.DWord
        
        # Check if the data type is valid
        if out is None:
            logger.error(f"Invalid data type with address {varAddr}.")
            return

        # Split the address to get the bit address
        if DT.Bit == out:
            bit = int(varAddr.split('.')[1])
            start = int(varAddr.split('.')[0][2:])
            if bit > 7:
                logger.error(f"Bit address must be less than 8 with address {varAddr}.")
                return
            varValue = bool(varValue) << bit # Convert the value to the corresponding bit
        else:
            # Split the address to get the start address
            start = int(varAddr[2:])

        # Write data to the PLC
        with lock:
            if varAddr[0].lower() == 'v':
                self.plc.db_write(1, start, varValue)
            else:
                self.plc.write_area(area, 0, start, varValue)
        
        if _DEBUG:
            logger.info(f"Write data to PLC: {varAddr}, {varValue}")


    def read_multiple_incoherent_bits(self, ls_varAddr: list, _DEBUG: bool = True) -> list:
        """
        Reads multiple bits incoherently from the PLC S7-200-SMART.

        Args:
            ls_varAddr (list): A list of addresses of the variables.

        Returns:
            varValue (list): A list of values of the variables.
        """
        varValue = []
        for varAddr in ls_varAddr:
            _, read_result = self.readData(varAddr)
            varValue.append(read_result)

        if _DEBUG:
            logger.info(f"Read data from PLC: \n{ls_varAddr} \n{varValue}")
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


    def reconnect(self, refVarAddr: str='VX200.1') -> None:
        """
        Reconnects to the PLC S7-200-SMART.

        Args:
            refVarAddr (str, optional): The address of the reference variable. Defaults to 'VX200.1'.

        Returns:
            None
        """
        count = 0
        case = 0
        while True:
            print(case)
            if case == 1:
                # connect
                logger.info(f"Connecting to PLC...")
                try:
                    self.plc.connect(self.host, self.rack, self.slot)
                    logger.info(f"Connected to PLC.")
                    case = 2
                except Exception as e:
                    logger.error(f"Error connecting to PLC: {e}")
                    case = 1
                    time.sleep(5)
            elif case == 2:
                # running => read cyclic the service level if it fails disconnect and unsubscribe => wait 5s => connect
                try:
                    _, service_level = self.readData(refVarAddr)

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
                    self.plc.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting from PLC: {e}")
                case = 0
            else:
                # wait
                case = 1
                time.sleep(5)


    def disconnect(self) -> None:
        """
        Disconnects from the PLC S7-200-SMART.
        """
        self.plc.disconnect()
        logger.info(f"Disconnected from PLC {self.host}.")