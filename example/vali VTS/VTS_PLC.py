from fablab_lib import PLC_S7_1200
from VTS_Variables import* 
from VTS_MQTT import client
import time

def datachange_notification(node, val, data):
    data_name = name_list[var_list.index(str(node))]
    print(str(data_name) + " : " + str(val))
    client.publish_data(data_name, val)

def write_data(node, data_name, data_value):
    if data_name == "setpoint":
        plc.writeData(node, data_value, 'WORD')
    elif data_name == "startup":
        plc.writeData(node, True, 'BOOL')
        time.sleep(0.1)
        plc.writeData(node, False, 'BOOL')
    elif data_name == "forward":
        plc.writeData(node, True, 'BOOL')
        time.sleep(0.1)
        plc.writeData(node, False, 'BOOL')
    elif data_name == "reverse":
        plc.writeData(node, True, 'BOOL')
        time.sleep(0.1)
        plc.writeData(node, False, 'BOOL')
    elif data_name == "stop":
        plc.writeData(node, True, 'BOOL')
        time.sleep(0.1)
        plc.writeData(node, False, 'BOOL')
    else:
        plc.writeData(node, data_value, 'BOOL')
    
    client.publish_data(data_name, data_value)

_HOST = '192.168.1.1'
_PORT = 4840

plc = PLC_S7_1200.PLC(host=_HOST, port=_PORT, nameStation='VTSauto', is_pc=is_pc)
plc.nodes_to_subscribe = var_list
plc.datachange_notification_ = datachange_notification
plc.connect()

for nodes in var_list:
    node = plc.plc.get_node(nodes)
    name_list[var_list.index(nodes)] = node.get_display_name().Text

plc.disconnect()
