from OMvsHT_VARs import *
from fablab_lib import spB
from fablab_lib import restart_raspberry
import ast

serverUrl = "40.82.154.13"
omGroupId = "group1"
omNodeId = "N03"
omDeviceId = "DV01"

htGroupId = "group1"
htNodeId = "N02"
htDeviceId = "DV01"

# --------------------- Setup - SparkPlugB ----------------------
########################### OMRON ########################################
def callback_message_omDevice(topic, payload, lsName, lsValue, lsDataType, lsTimestamp):
    omVar_name.clear()
    omVar_addr.clear()
    omOld_var.clear()
    print(omVar_name)
    print(omVar_addr)
    try:
        Payload.omPayloadDevice = payload
        print("Received MESSAGE: %s - %s" % (topic, payload))
        for name in lsName:
            value = lsValue[lsName.index(name)]
            if name == 'deviceProtocol' and value == 'FINS':
                print(value)
                omFINS_flag.set()

            elif name == 'deviceAddress':
                ip_PLC.omIPEthernet = value
                omCheckIP_flag.set()

            elif value.find('b') == 0:
                _var_addr = ast.literal_eval(value.encode().decode())
                omVar_name.append(name)
                omVar_addr.append(_var_addr)
                omOld_var.append(-1)
        print(omVar_name, 'count', len(omVar_name))
        print(omVar_addr, 'count', len(omVar_addr))
        print(omOld_var, 'count', len(omOld_var))

    except Exception as e:
        print(e)


def callback_message_omNode(topic, payload, lsName, lsValue, lsDataType, lsTimestamp):
    try:
        Payload.omPayloadNode = payload
        print("Received MESSAGE: %s - %s" % (topic, payload))

        for name in lsName:
            value = lsValue[lsName.index(name)]
            if name == 'Node Control/Rebirth' and value == True:
                omRebirth_flag.set()
                print('Rebirth')

            elif name == 'Node Control/Reboot' and value == True:
                print('Reboot')
                restart_raspberry()
    except Exception as e:
        print(e)


########################### HAITHIEN ########################################
def callback_message_htDevice(topic, payload, lsName, lsValue, lsDataType, lsTimestamp):
    htVar_name.clear()
    htVar_addr.clear()
    htOld_var.clear()
    print(htVar_name)
    print(htVar_addr)
    try:
        Payload.htPayloadDevice = payload
        print("Received MESSAGE: %s - %s" % (topic, payload))
        for name in lsName:
            value = lsValue[lsName.index(name)]
            if name == 'deviceProtocol' and value == 'OPC-UA':
                print(value)
                htOPCUA_flag.set()

            elif name == 'deviceAddress':
                ip_PLC.htIPEthernet = value
                htCheckIP_flag.set()

            elif value.find('ns') == 0:
                htVar_name.append(name)
                htVar_addr.append(value)
                htOld_var.append(-1)
        print(htVar_name, 'count', len(htVar_name))
        print(htVar_addr, 'count', len(htVar_addr))
        print(htOld_var, 'count', len(htOld_var))

        if init.htSub:
            init.htSub = 0
        else:
            htNodeSub_flag.set()

    except Exception as e:
        print(e)


def callback_message_htNode(topic, payload, lsName, lsValue, lsDataType, lsTimestamp):
    try:
        Payload.htPayloadNode = payload
        print("Received MESSAGE: %s - %s" % (topic, payload))

        for name in lsName:
            value = lsValue[lsName.index(name)]
            if name == 'Node Control/Rebirth' and value == True:
                htRebirth_flag.set()
                print('Rebirth')

            elif name == 'Node Control/Reboot' and value == True:
                print('Reboot')
                restart_raspberry()
    except Exception as e:
        print(e)
#--------------------------------------------------------------------------------------

def callback_on_connect(rc):
    ip_PLC.is_connect_wifi = 1
    print("Connected to MQTT broker with result code " + str(rc))


def callback_on_disconnect(rc):
    if rc != 0:
        ip_PLC.is_connect_wifi = 0
        wifi_disconnect_flag.set()
        print("Unexpected disconnection from MQTT broker!")

        Log.log_data('DEATH', None, 'N02/DV01', 'Siemens', ip_PLC.is_connect_wifi)
        Log.log_data('DEATH', None, 'N02', 'Siemens', ip_PLC.is_connect_wifi)
        Log.log_data('DEATH', None, 'N03/DV01', 'Omron', ip_PLC.is_connect_wifi)
        Log.log_data('DEATH', None, 'N03', 'Omron', ip_PLC.is_connect_wifi)


omDevice = spB(host=serverUrl, GroupId=omGroupId, NodeId=omNodeId, DeviceId=omDeviceId, levelEntity='device')
omDevice.on_message = callback_message_omDevice
omDevice.on_connect = callback_on_connect
omDevice.on_disconnect = callback_on_disconnect
omDevice.connect()

omNode = spB(host=serverUrl, GroupId=omGroupId, NodeId=omNodeId, levelEntity='node')
omNode.on_message = callback_message_omNode
omNode.connect()

htDevice = spB(host=serverUrl, GroupId=htGroupId, NodeId=htNodeId, DeviceId=htDeviceId, levelEntity='device')   
htDevice.on_message = callback_message_htDevice
htDevice.connect()

htNode = spB(host=serverUrl, GroupId=htGroupId, NodeId=htNodeId, levelEntity='node')
htNode.on_message = callback_message_htNode
htNode.connect()


# ------------------------ Tasks -------------------------------------
########################### OMRON ########################################
def task_omRebirth():
    var_string = ['deviceId', 'deviceProtocol', 'deviceAddress']
    while True:
        omRebirth_flag.wait()

        print(Payload.omPayloadNode)
        print(Payload.omPayloadDevice)
        print('Start Rebirth')

        if Payload.omPayloadNode is not None:
            for item in Payload.omPayloadNode['metrics']:
                if item['name'] == 'BDSEQ':
                    omNode.data_set_value(item['name'], int(item['value']))
                else:
                    omNode.data_set_value(item['name'], item['value'])
                omNode.publish_birth()
                # print(item)
            Log.log_data('BIRTH', None, 'N03', 'Omron', ip_PLC.is_connect_wifi)

        if Payload.omPayloadDevice is not None:
            for item in Payload.omPayloadDevice['metrics']:
                if item['name'] in var_string:
                    omDevice.data_set_value(item['name'], item['value'])
                else:
                    omDevice.data_set_value(item['name'], 0)
                omDevice.publish_birth()
                # print(item)
            Log.log_data('BIRTH', None, 'N03/DV01', 'Omron', ip_PLC.is_connect_wifi)

        omRebirth_flag.clear()

########################### HAITHIEN ########################################
def task_htRebirth():
    var_string = ['deviceId', 'deviceProtocol', 'deviceAddress']
    while True:
        htRebirth_flag.wait()

        if Payload.htPayloadNode is not None:
            for item in Payload.htPayloadNode['metrics']:
                if item['name'] == 'BDSEQ':
                    htNode.data_set_value(item['name'], int(item['value']))
                else:
                    htNode.data_set_value(item['name'], item['value'])
                htNode.publish_birth()
                # print(item)
            Log.log_data('BIRTH', None, 'N02', 'Siemens', ip_PLC.is_connect_wifi)

        if Payload.htPayloadDevice is not None:
            for item in Payload.htPayloadDevice['metrics']:
                if item['name'] in var_string:
                    htDevice.data_set_value(item['name'], item['value'])
                else:
                    htDevice.data_set_value(item['name'], 0)
                htDevice.publish_birth()
                # print(item)
            Log.log_data('BIRTH', None, 'N02/DV01', 'Siemens', ip_PLC.is_connect_wifi)

        htRebirth_flag.clear()

