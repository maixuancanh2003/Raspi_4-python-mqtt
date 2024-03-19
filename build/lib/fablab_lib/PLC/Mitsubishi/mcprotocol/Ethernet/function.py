"""
This file contains common functions to analyze data from a Mitsubishi FX5U PLC.

Library: pymelsec
Installation: pip install pymelsec
Information: This library supports Mitsubishi PLCs with Type 3E frame 
or Type 4E frame (FX5U, FX5UC, iQ-R, iQ-F, Q Series)
Another Protocol Name: SLMP (Seamless Message Protocol)
"""
import subprocess
import logging
import time
import threading
from .pymelsec import Type3E, Type4E
from .pymelsec.constants import DT

lock = threading.Lock()

# Application logger
logger = logging.getLogger("PLC_Mitsubishi")
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


def convert_logic_equation(bits, equation, _DEBUG: bool = False):
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
    if _DEBUG:
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
            port: int, 
            plc_type='Q', 
            frame='Type3E', 
            comm_type='binary', 
            nameStation: str=None,
            is_pc=False
        ) -> None:
        """
        Initializes a PLC object.

        Args:
            host (str): The IP address of the PLC.
            port (int): The port of the PLC.
            plc_type (str, optional): Connect PLC type. "Q", "L", "QnA", "iQ-L", "iQ-R". Defaults to 'Q'.
            frame (str, optional): The frame type ('Type3e' or 'Type4E'). Defaults to 'Type3E'.
            comm_type (str, optional): The communication type ('binary' or 'ascii'). Defaults to 'binary'.
            nameStation (str, optional): The name of the machine station. Defaults to None.
            is_pc (bool, optional): Specifies whether PC is connecting to PLC. Defaults to False for Raspberry Pi connection.
        """
        self.host = host
        self.port = port
        self.plc_type = plc_type
        self.frame = frame
        self.comm_type = comm_type
        self.nameStation = nameStation
        self.is_pc = is_pc

        if self.nameStation is not None:
            logger.name = f'PLC_Mitsubishi - {self.nameStation}'

        waiting_for_connection(self.host, self.is_pc)


    def connect(self) -> None:
        """
        Connects to the PLC Mitsubishi.
        """
        self.plc = Type3E(host=self.host, port=self.port, plc_type=self.plc_type)
        self.plc.set_access_opt(comm_type=self.comm_type)
        self.plc.connect(ip=self.host, port=self.port)

        logger.info(f"Connected to PLC {self.host}.")

    
    def readData(self, varAddr: str, varType: str, varSize=1, _DEBUG: bool = False):
        """
        Reads data from the PLC Mitsubishi.

        Args:
            varAddr (str): The address of the variable.
            varType (str): The type of the variable.
            varSize (int): The size of the variable.

        Returns:
            _varAddr (str): The address of the variable.
            _varValue (str): The value of the variable.
        """
        with lock:
            read_result = self.plc.batch_read(
                ref_device=varAddr,
                read_size=varSize, 
                data_type=varType, 
            )
        
        _varAddr = read_result[0].device
        _varValue = read_result[0].value

        if _DEBUG:
            logger.info(f"Read data from PLC: {_varAddr}, {_varValue}")
        return _varAddr, _varValue
    

    def writeData(self, varAddr: str, varValue, varType: str, _DEBUG: bool = False):
        """
        Writes data to the PLC Mitsubishi.

        Args:
            varAddr (str): The address of the variable.
            varValue (any): The value of the variable.
            varType (str): The type of the variable.

        Returns:
            None
        """
        with lock:
            self.plc.batch_write(
                ref_device=varAddr,
                write_value=varValue,
                data_type=varType,
            )
        
        if _DEBUG:
            logger.info(f"Write data to PLC: {varAddr}, {varValue}")


    def read_multiple_incoherent_bits(self, ls_varAddr: list, _DEBUG: bool = False) -> list:
        """
        Reads multiple bits incoherently from the Mitsubishi PLC.

        Args:
            ls_varAddr (list): A list of addresses of the variables.

        Returns:
            varValue (list): A list of values of the variables.
        """
        varValue = []
        for varAddr in ls_varAddr:
            with lock:
                # time.sleep(0.01)
                read_result = self.plc.batch_read(
                    ref_device=varAddr,
                    read_size=1,
                    data_type=DT.BIT,
                )
            varValue.append(bool(read_result[0].value))

        if _DEBUG:
            logger.info(f"Read data from PLC: \n{ls_varAddr} \n{varValue}")
        return varValue


    def checkLogicBits(self, bits: list, equation: str, _DEBUG: bool = False) -> bool:
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
        return convert_logic_equation(bits, equation, _DEBUG)


    def reconnect(self, bitAlwaysOnAddr='SM400') -> None:
        """
        Reconnects to the PLC Mitsubishi.

        Args:
            bitAlwaysOnAddr (str, optional): The address of the bit always on. Defaults to 'SM400'.
        """
        count = 0
        case = 0
        while True:
            print(case)
            if case == 1:
                # connect
                logger.info(f"Connecting to PLC...")
                try:
                    self.plc.connect(self.host, self.port)
                    logger.info(f"Connected to PLC.")
                    case = 2
                except Exception as e:
                    logger.error(f"Error connecting to PLC: {e}")
                    case = 1
                    time.sleep(5)
            elif case == 2:
                # running => read cyclic the service level if it fails disconnect and unsubscribe => wait 5s => connect
                try:
                    _, service_level = self.readData(bitAlwaysOnAddr, DT.BIT)

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
                    self.plc.close()
                except Exception as e:
                    logger.error(f"Error disconnecting from PLC: {e}")
                case = 0
            else:
                # wait
                case = 1
                time.sleep(5)


    def disconnect(self) -> None:
        """
        Disconnects from the PLC Mitsubishi.
        """
        self.plc.close()
        logger.info(f"Disconnected from PLC {self.host}.")