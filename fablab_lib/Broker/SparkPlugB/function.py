"""
This file contains the implementation of the SparkplugB class, which represents a SparkplugB object.
The SparkplugB class provides methods for connecting to an MQTT broker, publishing data and commands,
and handling MQTT callbacks.

The SparkplugB class also defines the ST class, which is used to define machine states.

Library: mqtt-sparkplug-wrapper
Installation: pip install mqtt-sparkplug-wrapper
Information:
    This library supports SparkplugB v1.0.0
    This library is a wrapper for the Eclipse Tahu MQTT Sparkplug implementation
"""

import logging
from fablab_lib.Broker.SparkPlugB.mqtt_spb_wrapper import MqttSpbEntityEdgeNode, MqttSpbEntityDevice

# Application logger
logger = logging.getLogger("SparkplugB")
logger.setLevel(logging.DEBUG)
_log_handle = logging.StreamHandler()
_log_handle.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s | %(message)s'))
logger.addHandler(_log_handle)


class ST:
    """
    Class to define machine states.
    """
    On = 0                          # On state
    Run = 1                         # Running state
    Idle = 2                        # Idle state (no orders, machine is running but paused)
    Alarm = 3                       # Alarm state
    Setup = 4                       # Setup state (maintenance)
    Off = 5                         # Off state
    Ready = 6                       # Ready state (power on, not idle, not in fault)
    Wifi_disconnect = 7             # WiFi disconnect state


class SparkplugB:
    """
    Class representing a SparkplugB object.

    Args:
        host (str): The MQTT broker host.
        port (int): The MQTT broker port.
        GroupId (str): The SparkplugB GroupId.
        NodeId (str): The SparkplugB NodeId.
        DeviceId (str): The SparkplugB DeviceId.
        levelEntity (str, optional): The level entity of the SparkplugB object. Defaults to 'Device'.

    Attributes:
        host (str): The MQTT broker host.
        port (int): The MQTT broker port.
        GroupId (str): The SparkplugB GroupId.
        NodeId (str): The SparkplugB NodeId.
        DeviceId (str): The SparkplugB DeviceId.
        levelEntity (str): The level entity of the SparkplugB object.
        user (str): The username for MQTT authentication.
        password (str): The password for MQTT authentication.
        _spB (MqttSpbEntityEdgeNode or MqttSpbEntityDevice): The MQTT SparkplugB entity.
        on_connect (function): Callback function when connected to MQTT broker.
        on_disconnect (function): Callback function when disconnected from MQTT broker.
        on_message (function): Callback function when a message is received.

    """

    def __init__(self, 
            host: str, 
            port: int=1883, 
            GroupId: str=None, 
            NodeId: str=None, 
            DeviceId: str=None, 
            levelEntity='device'
            ) -> None:
        
        self.host = host
        self.port = port
        self.GroupId = GroupId
        self.NodeId = NodeId
        self.DeviceId = DeviceId
        self.levelEntity = levelEntity
        self.user = 'user'    
        self.password = 'password'

        self._spB = None
        _DEBUG = True

        # Create the spB entity object
        if self.levelEntity.upper() == 'NODE':
            self._spB = MqttSpbEntityEdgeNode(self.GroupId, self.NodeId, _DEBUG)
        elif self.levelEntity.upper() == 'DEVICE':
            self._spB = MqttSpbEntityDevice(self.GroupId, self.NodeId, self.DeviceId, _DEBUG)
        else:
            raise Exception('Invalid levelEntity')

        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None

    def _on_message(self, topic, payload):
        """
        Internal callback function when a message is received.

        Args:
            topic (str): The MQTT topic.
            payload (dict): The MQTT message payload.

        """
        lsName = []
        lsValue = []
        lsDataType = []
        lsTimestamp = []

        try:
            logger.info("Received MESSAGE: %s - %s" % (topic, payload))
            print(payload['metrics'][0]['timestamp'])
            for item in payload['metrics']:
                # print(item.keys())
                if item['name'] == '' or item['value'] == '':
                    continue
                else:
                    lsName.append(item['name'])
                    lsValue.append(item['value'])
                    lsDataType.append(item['datatype'])
                    lsTimestamp.append(item['timestamp'])
            
        except Exception as e:
            logger.error("Error parsing message: %s" % e)

        # Call the on_message callback functions
        if self.on_message is not None:
            self.on_message(topic, dict(payload), lsName, lsValue, lsDataType, lsTimestamp)

    def _on_connect(self, rc):
        """
        Internal callback function when connected to MQTT broker.

        Args:
            rc (int): The result code of the connection.

        """
        logger.info("Connected to MQTT broker with result code %s" % str(rc))

        # Call the on_connect callback functions
        if self.on_connect is not None:
            self.on_connect(rc)

    def _on_disconnect(self, rc):
        """
        Internal callback function when disconnected from MQTT broker.

        Args:
            rc (int): The result code of the disconnection.

        """
        if rc != 0:
            logger.error("Unexpected disconnection from MQTT broker")

            # Call the on_disconnect callback functions
            if self.on_disconnect is not None:
                self.on_disconnect(rc)

    def connect(self):
        """
        Connect to the MQTT broker.

        """
        self._spB.on_connect = self._on_connect
        self._spB.on_disconnect = self._on_disconnect
        self._spB.on_message = self._on_message

        self._spB.connect(self.host, self.port, self.user, self.password)
    
    def disconnect(self):
        """
        Disconnect from the MQTT broker.

        """
        self._spB.disconnect()

    def Publish_Data(self, varName: str, varValue):
        """
        Publish data to the MQTT broker.

        Args:
            varName (str): The name of the variable.
            varValue: The value of the variable.

        """
        if self.levelEntity == 'Device':
            self._spB.publish_specific_data('DDATA', varName, varValue)
        elif self.levelEntity == 'Node':
            self._spB.publish_specific_data('NDATA', varName, varValue)

    def Publish_Command(self, varName: str, varValue):
        """
        Publish a command to the MQTT broker.

        Args:
            varName (str): The name of the variable.
            varValue: The value of the variable.

        """
        if self.levelEntity == 'Device':
            self._spB.publish_specific_data('DCMD', varName, varValue)
        elif self.levelEntity == 'Node':
            self._spB.publish_specific_data('NCMD', varName, varValue)

    def Publish_Birth(self, varName: str, varValue):
        """
        Publish birth data to the MQTT broker.

        Args:
            varName (str): The name of the variable.
            varValue: The value of the variable.

        """
        if self.levelEntity == 'Device':
            self._spB.publish_specific_data('DBIRTH', varName, varValue)
        elif self.levelEntity == 'Node':
            self._spB.publish_specific_data('NBIRTH', varName, varValue)

    def Publish_Death(self, status: int):
        """
        Publish death data to the MQTT broker.

        Args:
            status (int): The status of the death.

        """
        if self.levelEntity == 'Device':
            self._spB.publish_specific_data('DDEATH', 'bdSeq', status)
        elif self.levelEntity == 'Node':
            self._spB.publish_specific_data('NDEATH', 'bdSeq', status)
    
    def data_set_value(self, varName: str, varValue):
        """
        Set the value of a variable.

        Args:
            varName (str): The name of the variable.
            varValue: The value of the variable.

        """
        self._spB.data.set_value(varName, varValue)

    def data_get_value(self, varName: str):
        """
        Get the value of a variable.

        Args:
            varName (str): The name of the variable.

        Returns:
            varValue: The value of the variable.

        """
        return self._spB.data.get_value(varName)
    
    def attributes_set_value(self, varName: str, varValue):
        """
        Set the value of an attribute.

        Args:
            varName (str): The name of the attribute.
            varValue: The value of the attribute.

        """
        self._spB.attributes.set_value(varName, varValue)

    def attributes_get_value(self, varName: str):
        """
        Get the value of an attribute.

        Args:
            varName (str): The name of the attribute.

        Returns:
            varValue: The value of the attribute.

        """
        return self._spB.attributes.get_value(varName)

    def command_set_value(self, varName: str, varValue):
        """
        Set the value of a command.

        Args:
            varName (str): The name of the command.
            varValue: The value of the command.

        """
        self._spB.commands.set_value(varName, varValue)

    def command_get_value(self, varName: str):
        """
        Get the value of a command.

        Args:
            varName (str): The name of the command.

        Returns:
            varValue: The value of the command.

        """
        return self._spB.commands.get_value(varName)
    
    def publish_birth(self):
        """
        Publish birth data to the MQTT broker.

        """
        self._spB.publish_birth()

    def publish_data(self):
        """
        Publish data to the MQTT broker.

        """
        self._spB.publish_data()