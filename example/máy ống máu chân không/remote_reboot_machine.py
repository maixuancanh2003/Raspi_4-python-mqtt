import time
from mqtt_spb_wrapper import *

#--------------------------------------------------------------------

#--------------------------- Setup MQTT SPB -------------------------
def callback_message(topic, payload):
    global payload_node
    try:
        payload_node = dict(payload)
        print("Received MESSAGE: %s - %s" % (topic, payload))
    except Exception as e:
        print(e)

#------------------------------------------------------    
            
#------------------Initiate Mqtt SPB-----------------
# Create the spB entity object
GroupId = "WB"
NodeId = "OMCK"
DeviceId = "ClotActivator"

_DEBUG = True  # Enable debug messages

device = MqttSpbEntityDevice(GroupId, NodeId, DeviceId, _DEBUG)

device.on_message = callback_message  # Received messages

# Connect to the broker --------------------------------------------
serverUrl = "40.82.154.13"
_connected = False
while not _connected:
    print("Trying to connect to broker...")
    _connected = device.connect(serverUrl, 1883, "user", "password")
    if not _connected:
        print("  Error, could not connect. Trying again in a few seconds ...")
        time.sleep(3)
time.sleep(1)
#--------------------------------------------------------------------

# Send some telemetry values ---------------------------------------
if __name__ == '__main__':
        device.publish_specific_data('DCMD', 'Reboot', True)
        time.sleep(1)

        device.publish_specific_data('DCMD', 'Reboot', False)
        time.sleep(1)

        print("Disconnecting device")
        device.disconnect()

        print("Application finished !")