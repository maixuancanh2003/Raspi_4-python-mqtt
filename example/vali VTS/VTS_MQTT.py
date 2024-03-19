from fablab_lib import MQTT, spB
from fablab_lib import restart_raspberry
from VTS_MQTT import *
from VTS_Variables import *
from VTS_PLC import *

topic_standard = 'Test/VTSauto/AR_project/IOT_pub/'

# --------------------------- Publish data -------------------------------------
def publish_data(varName, varValue):
    client.publish_data(varName, varValue)
    Log.log_data(varName, "", varValue, "", ST.is_connectWifi)

# --------------------------- Setup MQTT -------------------------------------
# Define MQTT call-back function
def on_connect(client, rc):
    print('Connected to MQTT broker with result code ' + str(rc))
    # publish machine status
    client.publish_data('machineStatus', ST.Run)
    ST.is_connectWifi = 1


def on_disconnect(client, rc):
    if rc != 0:
        print('Unexpected disconnection from MQTT broker')
        ST.is_connectWifi = 0


def on_message(dataPayload, mqttName, mqttValue, mqttTimestamp):
        try:
            mqtt_name = mqttName
            mqtt_value = mqttValue

            if mqtt_name == 'setpoint':
                mqtt_value = int(mqtt_value)
            else:
                if mqtt_value == 'false':
                    mqtt_value = bool(False)
                elif mqtt_value == 'true':
                    mqtt_value = bool(True)
                    
        except Exception as e:
            print(e)

        if mqtt_name in name_list:
            nodeID = var_list[name_list.index(mqtt_name)]
            write_data(nodeID, mqtt_name, mqtt_value)
            

mqttBroker = '40.82.154.13'  # cloud
mqttPort = 1883
client = MQTT(host=mqttBroker, port=mqttPort)
client.standardTopic = topic_standard
client.en_subscribe = True
client.en_lastwill = True
client.topicSub = [f'Test/VTSauto/AR_project/IIOT_write/{i}' for i in name_list]
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.connect()

# --------------------------- Check data -------------------------------------
publish_data('machineStatus', ST.Run, ST.Run)

# --------------------------- Setup SparkPlugB  -------------------------------------
def callback_message_device(topic, payload):
    try:
        print("Received MESSAGE: %s - %s" % (topic, payload))

        for item in payload['metrics']:
            if item['name'] == 'Reboot' and item['value'] == True:
                print('REBOOT!')
                restart_raspberry()
    except Exception as e:
        print(e)

GroupId = "VTSauto"
NodeId = "Siemens"
DeviceId = "ValiSiemens"

device = spB(host=mqttBroker, port=mqttPort, GroupId=GroupId, NodeId=NodeId, DeviceId=DeviceId, levelEntity='device')
device.on_message = callback_message_device
device.connect()

