"""
This module contains classes and functions for working with Omron PLCs over Ethernet.

Library: fins
Installation: pip install fins
Protocol: FINS/TCP
Connection: Ethernet
Information: This library is used to communicate with Omron PLCs over Ethernet using the FINS/TCP protocol.
"""
import subprocess
import logging
import time
import threading
import fablab_lib.PLC.Omron.fins.Ethernet.fins.udp as fins
lock = threading.Lock() # Create a lock object

# Application logger
logger = logging.getLogger("PLC_Omron")
logger.setLevel(logging.DEBUG)
_log_handle = logging.StreamHandler()
_log_handle.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s | %(message)s'))
logger.addHandler(_log_handle)


class DT:
    """Data types for PLC memory areas."""
    BIT = b'\x00'
    WORD = b'\x82'
    COUNTER = b'\x81'
    TIMER = b'\x81'


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
    # print(lsVariables)

    # Replace variable names with corresponding bits
    for chr_ in lsVariables:
        if chr_.isalpha() and chr_.lower() in 'abcdefghijklmnopqrstuvwxyz':
            equation = equation.replace(chr_, str(int(bits[ord(chr_) - 97])))
    # print(equation)

    # Replace the logical operators with Python syntax
    equation = equation.replace('.', ' and ')
    equation = equation.replace('|', ' or ')
    equation = equation.replace('/', ' not ')
    # Remove all extra spaces from the equation
    equation = ' '.join(equation.split())
    # print(equation)

    # Evaluate the expression using eval
    result = bool(eval(equation))
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
            # port: int, 
            dest_node_add: int, 
            srce_node_add: int, 
            nameStation: str=None,
            is_pc=False) -> None:
        """
        Initializes a PLC object.

        Args:
            host (str): The IP address of the PLC.
            dest_node_add (int): The destination node address.
            srce_node_add (int): The source node address.
            nameStation (str, optional): The name of the machine station. Defaults to None.
            is_pc (bool, optional): Specifies whether the IP address belongs to a Laptop. Defaults to False for Raspberry Pi connection.
        """
        self.host = host
        # self.port = port
        self.dest_node_add = dest_node_add
        self.srce_node_add = srce_node_add
        self.nameStation = nameStation
        self.is_pc = is_pc

        if self.nameStation is not None:
            logger.name = f'PLC_Omron - {self.nameStation}'

        waiting_for_connection(self.host, self.is_pc)


    def connect(self) -> None:
        """
        Connects to the PLC Omron.
        """
        self.plc = fins.UDPFinsConnection()
        self.plc.connect(self.host)
        self.plc.dest_node_add = self.dest_node_add
        self.plc.srce_node_add = self.srce_node_add

        logger.info(f"Connected to PLC {self.host}.")


    def BCD_decode(self, data: bytes, decimals: int):
        """
        Decodes BCD-encoded data.

        Args:
            data (bytes): The BCD-encoded data.
            decimals (int): The number of decimal places.

        Returns:
            int: The decoded value.
        """
        res = 0
        for n, b in enumerate(reversed(data)):
            res += (b & 0x0F) * 10 ** (n * 2 - decimals)
            res += (b >> 4) * 10 ** (n * 2 + 1 - decimals)
        return res


    def readData_ver1(self, varAddr: bytes, varType: str, _DEBUG: bool = False):
        """
        Reads data from the PLC using the ver1 method.

        Args:
            varAddr (bytes): The address of the variable.
            varType (str): The type of the variable.

        Note: varType is considered only when reading WORD, COUNTER, BOOL, TIMER variables.

        Returns:
            tuple: The address and value of the variable.
        """
        # Check the variable type
        if varType.upper() == 'WORD':
            with lock:
                mem_area = self.plc.memory_area_read(DT.WORD, varAddr)
            varValue = self.BCD_decode(mem_area[-2:],0)
        elif varType.upper() == 'COUNTER':
            with lock:
                mem_area = self.plc.memory_area_read(DT.COUNTER, varAddr)
            varValue = self.BCD_decode(mem_area[-2:],0)
        elif varType.upper() == 'BOOL':
            with lock:
                mem_area = self.plc.memory_area_read(DT.BIT, varAddr)
            varValue = self.BCD_decode(mem_area[-1:],0)
        elif varType.upper() == 'TIMER':
            with lock:
                mem_area = self.plc.memory_area_read(DT.TIMER, varAddr)
            varValue = self.BCD_decode(mem_area[-2:],0)
        else:
            logger.error(f"Error reading data from PLC: {varAddr}, {varValue}, {varType}")
            return varAddr, None

        if _DEBUG:
            logger.info(f"Read successfully data from PLC: {varAddr}, {varValue}, {varType}")
        return varAddr, varValue
    

    def readData_ver2(self, varAddr: bytes, _DEBUG: bool = False):
        """
        Reads data from the PLC using the ver2 method.

        Args:
            varAddr (bytes): The address of the variable.

        Returns:
            tuple: The address and value of the variable.
        """
        memory_area = {
            'D': 'DM',
            'C': 'CNT',
            'CIO': 'CIO',
            'T': 'TIM',
        }
        # Check if the variable address contains a bit address
        if '-' in varAddr:
            temp = varAddr.split('-')
            area = temp[0]
            word_address = temp[1]
            bit_address = temp[2]
        else:
            area = varAddr[0]
            word_address = varAddr[1:]
            bit_address = 0

        try:
            with lock:
                varValue = self.plc.read(memory_area=memory_area[area], word_address=word_address, bit_address=bit_address)
            varValue = varValue[0]
        except Exception as e:
            logger.error(f"Error reading data from PLC: {e}")
            return varAddr, None

        if _DEBUG:
            logger.info(f"Read successfully data from PLC: {varAddr}, {varValue}")
        return varAddr, varValue


    def writeData_ver1(self, varAddr: bytes, varValue: bytes, varType: str, _DEBUG: bool = False):
        """
        Writes data to the PLC using the ver1 method.

        Args:
            varAddr (bytes): The address of the variable.
            varValue (bytes): The value to be written.
            varType (str): The type of the variable.

        Note: varType is considered only when writing WORD, COUNTER, BOOL, TIMER variables.

        Returns:
            None
        """
        # Check the variable type
        if varType.upper() == 'WORD':
            with lock:
                self.plc.memory_area_write(DT.WORD, varAddr, varValue)
        elif varType.upper() == 'COUNTER':
            with lock:
                self.plc.memory_area_read(DT.COUNTER, varAddr, varValue)
        elif varType.upper() == 'BOOL':
            with lock:
                self.plc.memory_area_read(DT.BIT, varAddr, varValue, 1)
        elif varType.upper() == 'TIMER':
            with lock:
                self.plc.memory_area_read(DT.TIMER, varAddr, varValue)
        else:
            logger.error(f"Error writing data to PLC: {varAddr}, {varValue}, {varType}")
            return

        if _DEBUG:
            logger.info(f"Write successfully data to PLC: {varAddr}, {varValue}, {varType}")


    def writeData_ver2(self, varAddr: bytes, varValue, _DEBUG: bool = False):
        """
        Writes data to the PLC using the ver2 method.

        Args:
            varAddr (bytes): The address of the variable.
            varValue: The value to be written.

        Returns:
            None
        """
        memory_area = {
            'D': 'DM',
            'C': 'CNT',
            'CIO': 'CIO',
            'T': 'TIM',
        }
        # Check if the variable address contains a bit address
        if '-' in varAddr:
            temp = varAddr.split('-')
            area = temp[0]
            word_address = temp[1]
            bit_address = temp[2]
        else:
            area = varAddr[0]
            word_address = varAddr[1:]
            bit_address = 0
        try:
            with lock:
                self.plc.write(value=varValue, memory_area=memory_area[area], word_address=word_address, bit_address=bit_address)
        except Exception as e:
            logger.error(f"Error writing data to PLC: {e}")
            return
        
        if _DEBUG:
            logger.info(f"Write successfully data to PLC: {varAddr}, {varValue}")


    def read_multiple_incoherent_bits_ver1(self, ls_varAddr: list, _DEBUG: bool = False) -> list:
        """
        Reads multiple incoherent bits from the PLC using the ver1 method.

        Args:
            ls_varAddr (list): A list of variable addresses.

        Returns:
            list: A list of values corresponding to the variable addresses.
        """
        varValue = []
        for varAddr in ls_varAddr:
            # Read data for each variable address
            _, read_result = self.readData_ver1(varAddr, 'BIT')
            varValue.append(bool(read_result))

        if _DEBUG:
            logger.info(f"Read data from PLC: \n{ls_varAddr} \n{varValue}")
        return varValue
    

    def read_multiple_incoherent_bits_ver2(self, ls_varAddr: list, _DEBUG: bool = False) -> list:
        """
        Reads multiple incoherent bits from the PLC using the ver2 method.

        Args:
            ls_varAddr (list): A list of variable addresses.

        Returns:
            list: A list of values corresponding to the variable addresses.
        """
        varValue = []
        for varAddr in ls_varAddr:
            _, read_result = self.readData_ver2(varAddr)
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


    def reconnect(self, bitAlwaysOnAddr=b'\x00\x00\x00') -> None:
        """
        Reconnects to the PLC Omron.

        Args:
            bitAlwaysOnAddr (str, optional): The address of the bit always on. Defaults to b'\x00\x00\x00'.

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
                    self.plc.connect(self.host)
                    logger.info(f"Connected to PLC.")
                    case = 2
                except Exception as e:
                    logger.error(f"Error connecting to PLC: {e}")
                    case = 1
                    time.sleep(5)
            elif case == 2:
                # running => read cyclic the service level if it fails disconnect and unsubscribe => wait 5s => connect
                try:
                    _, service_level = self.readData_ver1(bitAlwaysOnAddr, 'BOOL')

                    logger.info(f"Service level: {service_level}")
                    if service_level:
                        count += 1
                        case = 2
                        time.sleep(0.2)
                        if count == 5:
                            count = 0
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
                    self.plc.__del__()
                except Exception as e:
                    logger.error(f"Error disconnecting from PLC: {e}")
                case = 0
            else:
                # wait
                case = 1
                time.sleep(5)


    def disconnect(self) -> None:
        """
        Disconnects from the PLC Omron.
        """
        self.plc.__del__()
        logger.info(f"Disconnected from PLC {self.host}.")