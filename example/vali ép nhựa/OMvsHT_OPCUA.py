from OMvsHT_Spb import*
from fablab_lib import generate_data
from fablab_lib import PLC_S7_1200

#--------------------------- Functions --------------------------------
def datachange_notification(node, val, data):
    try:
        dataName = htVar_name[htVar_addr.index(str(node))]
        dataValue = val
        htPublish_data(dataName, dataValue, node)
    except Exception as e:
        print(e)
        htReconnectPLC_flag.set()


def htPublish_data(data_name, data_value, node):
    data_post = generate_data(data_name, data_value)
    htDevice.Publish_Data(data_name, data_value)
    print(data_post)
    Log.log_data(data_name, node, data_value, 'Siemens', ip_PLC.is_connect_wifi)


def htResetProgramSIEMENS():
    try:
        htOPCUA_instance.writeData(bitReset.ht, True, 'BOOL')
        threading.Event().wait(0.1)
        htOPCUA_instance.writeData(bitReset.ht, False, 'BOOL')
        print("Reset SIEMENS successfully")
    except Exception as e:
        print(e)
        htReconnectPLC_flag.set()


def on_connect_opcua(status):
    if status:
        htPLC_connected_flag.set()
    else:
        htReconnectPLC_flag.set()


def on_subscribe_opcua(_subscription, self):
    global subscription_handle_list, subscription

    subscription_handle_list = self.subscription_handle_list
    subscription = _subscription

# ------------------------ Tasks -------------------------------------
def task_htRead_data_plc():
    global htOPCUA_instance, is_pc
    """
    -handles connect/disconnect/reconnect/subscribe/unsubscribe
    -connection-monitoring with cyclic read of the service-level
    """
    htOPCUA_flag.wait()
    htCheckIP_flag.wait()

    htOPCUA_instance = PLC_S7_1200.PLC(ip_PLC.htIPEthernet, is_pc=is_pc)
    htOPCUA_instance.nodes_to_subscribe = htVar_addr.copy()
    htOPCUA_instance.datachange_notification_ = datachange_notification
    htOPCUA_instance.on_connect_opcua = on_connect_opcua
    htOPCUA_instance.on_subscribe_opcua = on_subscribe_opcua
    htOPCUA_instance.opcua_client()


def task_htSubcribe_node_opcua():
    global subscription_handle_list, subscription
    htOPCUA_flag.wait()
    htPLC_connected_flag.wait()

    print('task_htSubcribe_node_opcua')

    while True:
        try:
            htNodeSub_flag.wait()

            htOPCUA_instance.nodes_to_subscribe = htVar_addr.copy()
            print('Subcribing Node again...')

            print(subscription_handle_list)
            for item in subscription_handle_list:
                subscription.unsubscribe(item)
            subscription_handle_list.clear()
            
            htOPCUA_instance.nodes_to_subscribe = htVar_addr.copy()
            for nodes in htVar_addr:
                node_ = htOPCUA_instance.get_node(nodes)
                subscription_handle_list.append(subscription.subscribe_data_change(node_))
            print(subscription_handle_list)
            htNodeSub_flag.clear()

        except Exception as e:
            print(e)
            print('Siemens - Failed task_htSubcribe_node_opcua!')
            htNodeSub_flag.clear()

