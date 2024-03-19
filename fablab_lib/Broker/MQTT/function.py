"""
This module contains the MQTT class.

Library: paho-mqtt
Installation: pip install paho-mqtt
Information: https://pypi.org/project/paho-mqtt/

This module contains the MQTT class, which is responsible for connecting to an MQTT broker and publishing/subscribing to topics.
"""

from fablab_lib.Broker.JsonPayload.function import generate_data
import fablab_lib.Broker.MQTT.paho.mqtt.client as mqtt
import time
import logging
import json
import threading

lock = threading.Lock()

# Application logger
logger = logging.getLogger("MQTT")
logger.setLevel(logging.DEBUG)
_log_handle = logging.StreamHandler()
_log_handle.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s | %(message)s'))
logger.addHandler(_log_handle)


# Variables to store machine states
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


class MQTT:
    """
    Initialize the MQTT Client.

    Args:
        host (str, optional): The MQTT broker host. Defaults to 'localhost'.
        port (int, optional): The MQTT broker port. Defaults to 1883.
        keepalive (int, optional): The keepalive time in seconds. Defaults to 45.
        user (str, optional): The username for authentication. Defaults to "".
        password (str, optional): The password for authentication. Defaults to "".
        use_tls (bool, optional): Specifies whether to use TLS encryption. Defaults to False.
        tls_ca_path (str, optional): The path to the CA certificate. Defaults to "".
        tls_cert_path (str, optional): The path to the client certificate. Defaults to "".
        tls_key_path (str, optional): The path to the client key. Defaults to "".
        timeout (int, optional): The connection timeout in seconds. Defaults to 5.

    Raises:
        ValueError: If standard topic is not set.
    """

    def __init__(self, 
            host: str, 
            port: int, # Common: 1883 
            keepalive=45,
            user="",
            password="",
            use_tls=False,
            tls_ca_path="",
            tls_cert_path="",
            tls_key_path="",
            timeout=5
            ):

        self.host = host
        self.port = port   
        self.keepalive = keepalive  # seconds
        self.user = user
        self.password = password
        self.use_tls = use_tls
        self.tls_ca_path = tls_ca_path
        self.tls_cert_path = tls_cert_path
        self.tls_key_path = tls_key_path
        self.timeout = timeout

        self.standardTopic = None
        self._mqtt = None # Mqtt client object

        # Callback function when a command is received
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None

        self.en_subscribe = False   # Enable subscribe to standard topic
        self.en_lastwill = False    # Enable last will message

        self.topicSub = None        # Topic to subscribe to


    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback function when the MQTT _mqtt is connected to the broker.

        Args:
            _mqtt: The MQTT _mqtt instance.
            userdata: The user data.
            flags: The connection flags.
            rc: The result code.
        """
        logger.info('Connected to MQTT broker with result code ' + str(rc))

        if self.en_subscribe:
            # Subscribe to standard topic
            topic = self.standardTopic
            if self.topicSub is not None:
                topic = self.topicSub
                # Check if topic is list
                if topic is list:
                    for t in topic:
                        self._mqtt.subscribe(t)
                        logger.info("Subscribed to MQTT topic: %s" % (t))
                else:
                    self._mqtt.subscribe(topic)
                    logger.info("Subscribed to MQTT topic: %s" % (topic))
            else:
                self._mqtt.subscribe(topic)
                logger.info("Subscribed to MQTT topic: %s" % (topic))
        
        # If on_connect callback is set, call it with the result code
        if self.on_connect is not None:
            self.on_connect(self, rc)


    def _on_disconnect(self, client, userdata, rc):
        """
        Callback function when the MQTT _mqtt is disconnected from the broker.

        Args:
            _mqtt: The MQTT _mqtt instance.
            userdata: The user data.
            rc: The result code.
        """
        if rc != 0:
            logger.error('Unexpected disconnection from MQTT broker')
            
            # If on_disconnect callback is set, call it with the result code
            if self.on_disconnect is not None:
                self.on_disconnect(self, rc)
    

    def _on_message(self, client, userdata, message):
        """
        Callback function when a message is received.

        Args:
            _mqtt: The MQTT _mqtt instance.
            userdata: The user data.
            message: The received message.
        """
        logger.info('Message received: ' + message.payload.decode())
        with lock:
            try:
                dataPayload = json.loads(message.payload.decode('utf-8').replace("[","").replace("]",""))
            except:
                try:
                    dataPayload = json.loads(message.payload.decode('utf-8'))
                except:
                    logger.error('Message is not JSON format')
                    return
            
            mqttName = dataPayload['name']
            mqttValue = dataPayload['value']
            mqttTimestamp = dataPayload['timestamp']

        # If on_message callback is set, call it with the received data
        if self.on_message is not None:
            self.on_message(self, dataPayload, mqttName, mqttValue, mqttTimestamp)


    def connect(self):
        """
        Connect to the MQTT broker.

        Returns:
            bool: True if connected successfully, False otherwise.
        """

        # If we are already connected, then exit
        if self.is_connected():
            return True

        # MQTT Client configuration
        if self._mqtt is None:
            self._mqtt = mqtt.Client(userdata=self)

        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_disconnect = self._on_disconnect
        self._mqtt.on_message = self._on_message

        if self.user != "":
            self._mqtt.username_pw_set(self.user, self.password)

        # If client certificates are provided
        if self.tls_cert_path and self.tls_cert_path and self.tls_key_path:
            logger.debug("Setting CA client certificates")
            import ssl
            self._mqtt.tls_set(ca_certs=self.tls_cert_path, certfile=self.tls_cert_path, keyfile=self.tls_key_path, cert_reqs=ssl.CERT_NONE)
            # self._mqtt.tls_insecure_set(True)

        #If only CA is proviced.
        elif self.tls_cert_path:
            logger.debug("Setting CA certificate")
            self._mqtt.tls_set(ca_certs=self.tls_ca_path)

        # If TLS is enabled
        else:
            if self.use_tls:
                self._mqtt.tls_set()    # Enable TLS encryption

        # Check if standard topic is set
        if self.standardTopic is None:
            logger.error('Standard topic is not set.')
            raise ValueError('Standard topic is not set.')
        
        if self.en_lastwill:
            # if machine is immediately turned off --> last_will sends 'Status: Off' to topic
            self._mqtt.will_set(self.standardTopic + 'machineStatus', str(generate_data('machineStatus', ST.Off)), 1, 1)
        
        # MQTT Connect
        logger.info('Trying to connect MQTT broker %s:%d' % (self.host, self.port))
        try:
            self._mqtt.connect(self.host, self.port, self.keepalive)
        except Exception as e:
            logger.warning('Error connecting to MQTT broker: ' + str(e))
            # return False
        
        # Start a background thread to handle MQTT messages
        self._mqtt.loop_start()
        logger.info('Connected to MQTT broker')
        time.sleep(0.1)

        # Wait some time to get connected
        _timeout = time.time() + self.timeout
        while not self.is_connected() and _timeout > time.time():
            time.sleep(0.1)

        # Return if we connected successfully
        return self.is_connected()


    def is_connected(self):
        if self._mqtt is None:
            return False
        else:
            return self._mqtt.is_connected()


    def publish_data(self, Name: str, Value, is_payload=False):
        """
        Publish data to a topic.

        Args:
            Name (str): The name of the data.
            Value: The value of the data.
            is_payload (bool, optional): Specifies whether to publish the data as a payload. Defaults to False.
        """
        topic = self.standardTopic + Name
        if is_payload:
            payload = str(Value)
        else:
            payload = str(generate_data(Name, Value))
        logger.info(f'Publishing data to topic {topic}: \n{payload}')
        # print(str(payload))
        # with lock:
        self._mqtt.publish(topic, payload, 1, 1)


    def subscribe(self, topic: str):
        """
        Subscribe to a topic.

        Args:
            topic (str): The topic to subscribe to.
        """
        logger.info('Subscribing to topic: ' + topic)
        self._mqtt.subscribe(topic)


    def disconnect(self):
        """
        Disconnect from the MQTT broker.
        """
        self._mqtt.loop_stop()
        self._mqtt.disconnect()
        logger.info('Disconnected from MQTT broker')
