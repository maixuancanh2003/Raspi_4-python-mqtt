from OMvsHT_Spb import*
from fablab_lib import generate_data
from fablab_lib import PLC_Omron
import time
from datetime import datetime

# --------------------------- Functions --------------------------------
def omPublish_data(data_name, data_value, data_addr):
    data_post = generate_data(data_name, data_value)
    omDevice.Publish_Data(data_name, data_value)
    print(data_post)
    Log.log_data(data_name, data_addr, data_value, 'Omron', ip_PLC.is_connect_wifi)


def omResetProgramOMRON():
    try:
        omFINS_instance.writeData_ver1(bitReset.om, b'\x00\x1f', 'BOOL')
        threading.Event().wait(0.1)
        omFINS_instance.writeData_ver1(bitReset.om, b'\x00\x00', 'BOOL')
        print("Reset OMRON successfully")
    except Exception as e:
        print(e)
        omReconnectPLC_flag.set()


def omFINS_getData(data_bytes, data_type):
    try:
        _, fins_data_value = omFINS_instance.readData_ver1(data_bytes, data_type)
        if data_type == 'WORD':
            fins_data_name = omVar_name[omVar_addr.index(data_bytes)]
        elif data_type == 'BOOL':
            fins_data_name = 'Signal'

        return(fins_data_name, fins_data_value)
    except Exception as e:
        print(e)
        omReconnectPLC_flag.set()

# ------------------------ Tasks -------------------------------------

def task_omCheckIP_PLC():
    global omFINS_instance, is_pc
    omFINS_flag.wait()
    omCheckIP_flag.wait()

    omFINS_instance = PLC_Omron.PLC(host=ip_PLC.omIPEthernet, dest_node_add=1, srce_node_add=15, is_pc=is_pc)
    omFINS_instance.connect()

    omPLC_connected_flag.set()


def task_omRead_data_plc():
    omFINS_flag.wait()
    omPLC_connected_flag.wait()

    while True:
        try:
            for data_bytes in omVar_addr:
                om1_flag.wait()

                if omVar_name[omVar_addr.index(data_bytes)] in omVar_fake:
                    continue
                data_name, data_value = omFINS_getData(data_bytes, 'WORD')
                data_value = data_value/10

                if (data_value != omOld_var[omVar_addr.index(data_bytes)]):
                    omPublish_data(data_name, data_value, data_bytes)
                    omOld_var[omVar_addr.index(data_bytes)] = data_value
                threading.Event().wait(0.1)

        except Exception as e:
            print(e)
            print("Omron - Failed task_omRead_data_plc!")
            time.sleep(1)
            omReconnectPLC_flag.set()


def task_omCount_cycleTime():
    omFINS_flag.wait()
    omPLC_connected_flag.wait()

    signal_byte = b'\x00\x05\x06'
    counterShot = 0
    _, prev_sign = omFINS_getData(signal_byte, 'BOOL')
    oldTime = datetime.now()

    while True:
        try:
            om2_flag.wait()
            _, new_sign = omFINS_getData(signal_byte, 'BOOL')

            if new_sign != prev_sign:
                print(prev_sign, new_sign)
                if prev_sign == 1 and new_sign == 0  :

                    newTime = datetime.now()
                    deltaTime = newTime - oldTime
                    counterShot += 1

                    data_name = 'cycleTime'
                    data_value = deltaTime.total_seconds()
                    if (data_name in omVar_name):
                        omPublish_data(data_name, data_value, signal_byte)

                    data_name = 'counterShot'
                    data_value = counterShot
                    if (data_name in omVar_name):
                        omPublish_data(data_name, data_value, signal_byte)

                    oldTime = newTime
                prev_sign = new_sign   
                    
            threading.Event().wait(0.05)

        except Exception as e:
            print(e) 
            print('Omron - Failed task_omCount_cycleTime!')
            time.sleep(1)
            omReconnectPLC_flag.set()