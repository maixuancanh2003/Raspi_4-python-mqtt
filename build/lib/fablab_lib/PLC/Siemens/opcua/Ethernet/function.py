"""
This module contains functions and classes related to the Siemens S7 1200 PLC and Ethernet communication.
It provides functionality to check the Ethernet connection, wait for the connection to be active, convert logic equations,
and interact with the PLC using OPC UA protocol.

Functions:
- is_ethernet_connected: Checks if the Ethernet connection to a specified IP address is active.
- waiting_for_connection: Waits for the Ethernet connection to be active.
- get_variables_from_equation: Extracts all unique variables from a given equation.
- convert_logic_equation: Converts a logic equation into a boolean result based on given bits.
- DictAsAttributes: A class that converts a dictionary to attributes.
- PLC: A class representing the PLC S7 1200.

Note: This code requires the opcua library to be installed.
"""
import subprocess
import logging
import time
import threading
from opcua import Client, ua, Node

lock = threading.Lock()

# Application logger
logger = logging.getLogger("PLC_S7 1200")
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
            logger.warning(f"Ethernet connection to {host} is not active.")  
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


class SubscriptionHandler:  
    """
    Subscription Handler. To receive events from server for a subscription
    This class is just a sample class. Whatever class having these methods can be used
    """
    def __init__(self, datachange_notification_, event_notification_, status_change_notification_):
        self.datachange_notification_ = datachange_notification_
        self.event_notification_ = event_notification_
        self.status_change_notification_ = status_change_notification_

    def datachange_notification(self, node: Node, val, data):
        """
        called for every datachange notification from server
        """
        print("Python: New data change event", node, val)
        if self.datachange_notification_ is not None:
            self.datachange_notification_(node, val, data)

    def event_notification(self, event: ua.EventNotificationList):
        """
        called for every event notification from server
        """
        print("Python: New event", event)
        if self.event_notification_ is not None:
            self.event_notification_(event)

    def status_change_notification(self, status: ua.StatusChangeNotification):
        """
        called for every status change notification from server
        """
        print("Python: New status", status)
        if self.status_change_notification_ is not None:
            self.status_change_notification_(status)


class PLC:
    def __init__(self, host: str, port: int=4840, nameStation: str=None, is_pc=False) -> None:
        """
        Initializes the PLC S7 1200.
        
        Args:
            host (str): The IP address of the PLC.
            port (int, optional): The port of the PLC. Defaults to 4840.
            nameStation (str, optional): The name of the machine station. Defaults to None.
            is_pc (bool, optional): Specifies whether the IP address belongs to a Laptop. Defaults to False for Raspberry Pi connection.
            
        Returns:
            None
        """
        self.host = host
        self.port = port
        self.nameStation = nameStation
        self.is_pc = is_pc

        self.url = f"opc.tcp://{self.host}:{self.port}"

        # Callback functions
        self.datachange_notification_ = None
        self.event_notification_ = None
        self.status_change_notification_ = None

        self.nodes_to_subscribe = None
        self.events_to_subscribe = None
        self.on_connect_opcua = None
        self.on_subscribe_opcua = None

        if self.nameStation is not None:
            logger.name = f'PLC_S7_1200 - {self.nameStation}'

        waiting_for_connection(self.host, self.is_pc)


    def opcua_client(self) -> None:
        """
        If subscription is needed, this method should be called instead of connect().

        Handles connect/disconnect/reconnect/subscribe/unsubscribe.
        Connection-monitoring with cyclic read of the service-level.
        """
        if self.nodes_to_subscribe is None:
            logger.error("No nodes to subscribe.")
            return
        
        self.client = Client(self.url)

        handler = SubscriptionHandler(self.datachange_notification_, self.event_notification_, self.status_change_notification_)
        subscription = None
        case = 0
        self.subscription_handle_list = []

        while True:
            print(case)
            if case == 1:
                # connect
                logger.info(f"Connecting...")
                try:
                    self.client.connect()
                    self.client.load_type_definitions()
                    logger.info(f"Connected.")

                    if self.on_connect_opcua is not None:
                        self.on_connect_opcua(status=True)

                    case = 2
                except Exception as e:
                    logger.error(f"Error connecting to PLC: {e}")
                    case = 1
                    time.sleep(5)
            elif case == 2:
                # subscribe all nodes and events
                logger.info(f"Subscribing nodes and events...")
                try:
                    subscription = self.client.create_subscription(50, handler)
                    self.subscription_handle_list = []

                    if self.nodes_to_subscribe:
                        for node in self.nodes_to_subscribe:
                            handle = subscription.subscribe_data_change(self.client.get_node(node))
                            self.subscription_handle_list.append(handle)
                    if self.events_to_subscribe:
                        for event in self.events_to_subscribe:
                            handle = subscription.subscribe_events(event[0], event[1])
                            self.subscription_handle_list.append(handle)

                    if self.on_subscribe_opcua is not None:
                        self.on_subscribe_opcua(subscription, self)

                    logger.info(f"Subscribed.")
                    case = 3
                except Exception as e:
                    logger.error(f"Error subscribing to nodes and events: {e}")
                    case = 4
                    time.sleep(0)
            elif case == 3:
                # running => read cyclic the service level if it fails disconnect and unsubscribe => wait 5s => connect
                try:
                    with lock:
                        service_level = self.client.get_node("ns=0;i=2267").get_value()
                    if service_level >= 200:
                        case = 3
                    else:
                        case = 4
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"Error during operation: {e}")
                    case = 4
            elif case == 4:
                # disconnect clean = unsubscribe, delete subscription then disconnect
                logger.info(f"Unsubscribing...")
                try:
                    if self.subscription_handle_list:
                        for handle in self.subscription_handle_list:
                            subscription.unsubscribe(handle)
                    subscription.delete()
                    logger.info(f"Unsubscribed.")

                except Exception as e:
                    logger.error(f"Error unsubscribing: {e}")
                    subscription = None
                    self.subscription_handle_list = []
                    time.sleep(0)

                logger.info(f"Disconnecting...")
                try:
                    self.client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting: {e}")

                if self.on_connect_opcua is not None:
                    self.on_connect_opcua(status=False)
                case = 0
            else:
                # wait
                case = 1
                time.sleep(5)

    
    def connect(self) -> None:
        """
        Connects to the PLC S7 1200.

        Returns:
            None

        Note: This method is not used if subscription is needed. Use opcua_client() instead.
        If don't need subscription, use this method.
        """
        self.plc = Client(self.url)
        self.plc.connect()
        logger.info(f"Connected to PLC {self.host}.")


    def readData(self, node: str, _DEBUG: bool=False):
        """
        Reads data from the PLC S7 1200.

        Args:
            node (str): The address of the variable.

        Returns:
            _name (str): The name of the variable.
            _value (any): The value of the variable.
        
        Note: This method is not used if subscription is needed. Use opcua_client() instead.
        """
        with lock:
            _node = self.plc.get_node(node)
            _value = _node.get_value()
            _name = _node.get_display_name().Text
            # _name = _node.nodeid.__dict__['Identifier']
        if _DEBUG:
            logger.info(f"Read data from PLC: {_name}, {_value}")
        return _name, _value
    

    def writeData(self, node: str, value, type: str, _DEBUG: bool = True) -> None:
        """
        Writes data to the PLC S7 1200.

        Args:
            node (str): The address of the variable.
            value (any): The value of the variable.
            type (str): The type of the variable.

            Note: The type must be one of the following: 'BOOL', 'BYTE', 'WORD', 'DWORD', 'INT', 'DINT', 'REAL', 'STRING', 'DATE_TIME'.

        Returns:
            None
        """
        with lock:
            _node = self.plc.get_node(node)
            if type == 'BOOL':
                _node.set_attribute(ua.AttributeIds.value, ua.DataValue(bool(value)))
            elif type == 'BYTE':
                _node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.Byte)))
            elif type == 'WORD':
                _node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.UInt16)))
            elif type == 'DWORD':
                _node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.UInt32)))
            elif _node == 'INT':
                _node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.Int16)))
            elif _node == 'DINT':
                _node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.Int32)))
            elif _node == 'REAL':
                _node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.Float)))
            elif _node == 'STRING':
                _node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.String)))
            elif _node == 'DATE_TIME':
                _node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.DateTime)))
            else:
                logger.error(f"Invalid type: {type}")
                return

        if _DEBUG:
            logger.info(f"Write data to PLC: {node}, {value}")


    def get_node(self, node: str) -> Node:
        """
        Gets the node from the PLC S7 1200.

        Args:
            node (str): The address of the variable.

        Returns:
            Node: The node of the variable.
        """
        with lock:
            _node = self.plc.get_node(node)
        
        return _node

    
    def read_multiple_incoherent_bits(self, ls_nodes: list, _DEBUG: bool = True) -> list:
        """
        Reads multiple bits incoherently from PLC S7 1200.

        Args:
            ls_varAddr (list): A list of addresses of the variables.

        Returns:
            varValue (list): A list of values of the variables.
        """
        varValue = []
        for varNode in ls_nodes:
            _, read_result = self.readData(varNode)
            varValue.append(bool(read_result))

        if _DEBUG:
            logger.info(f"Read data from PLC: \n{ls_nodes} \n{varValue}")
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


    def reconnect(self, refNodeAddr: str="ns=0;i=2267") -> None:
        """
        Reconnects to the PLC S7 1200.

        Args:
            refVarAddr (str, optional): The address of the reference variable. Defaults to "ns=0;i=2267".

        Returns:
            None
        
        Note: This method is not used if subscription is needed. Use opcua_client() instead.
        """
        case = 0
        count = 0
        while True:
            print(case)
            if case == 1:
                # connect
                logger.info(f"Connecting...")
                try:
                    self.client.connect()
                    self.client.load_type_definitions()
                    logger.info(f"Connected.")

                    case = 2
                except Exception as e:
                    logger.error(f"Error connecting to PLC: {e}")
                    case = 1
                    time.sleep(5)
            elif case == 2:
                # running => read cyclic the service level if it fails disconnect and unsubscribe => wait 5s => connect
                try:
                    with lock:
                        service_level = self.client.get_node(refNodeAddr).get_value()
                    if service_level >= 200:
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
                logger.info(f"Disconnecting...")
                try:
                    self.client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting: {e}")
                case = 0
            else:
                # wait
                case = 1
                time.sleep(5)
    

    def create_subscription(self, interval: int=50, handler=SubscriptionHandler) -> None:
        """
        Creates a subscription to the PLC S7 1200.

        Args:
            interval (int, optional): The interval of the subscription. Defaults to 50.
            handler (SubscriptionHandler, optional): The subscription handler.

        Returns:
            None
        """
        self.subscription = self.client.create_subscription(interval, handler)


    def subscribe_data_change(self, node: Node) -> None:
        """
        Subscribes to data change of a node.

        Args:
            node (Node): The node to subscribe.

        Returns:
            None
        """
        self.subscription.subscribe_data_change(node)
    
    
    def subscribe_events(self, event: Node, handler) -> None:
        """
        Subscribes to events of a node.

        Args:
            event (Node): The node to subscribe.
            handler (SubscriptionHandler): The subscription handler.

        Returns:
            None
        """
        self.subscription.subscribe_events(event, handler)


    def disconnect(self) -> None:
        """
        Disconnects from the PLC S7 1200.
        """
        self.plc.close()
        logger.info(f"Disconnected from PLC {self.host}.")
