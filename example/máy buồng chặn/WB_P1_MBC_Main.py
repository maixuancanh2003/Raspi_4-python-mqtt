from WB_P1_MBC_Variables import *
from WB_P1_MBC_MQTT import *
from WB_P1_MBC_PLC import *

# time.sleep(10)
#---------------------------------------------------------------------------
def task_data_setting_process():
    for i in range(dset_length):
        time.sleep(0.01)
        t1_interupt.wait()
        try:
            _, read_result = plc.readData(dset_addr[i], dset_type[i])
            real_value = read_result/100
            publish_data(dset_name[i], dset_addr[i], real_value, 'Setting')
            dset_old[i] = read_result

        except Exception as e:
            print('task_data_setting_process')
            print(e)
            reConEth_flg.set()

    while True:
        for i in range(dset_length):
            time.sleep(10)
            t1_interupt.wait()
            try:
                _, read_result = plc.readData(dset_addr[i], dset_type[i])
                if dset_old[i] != read_result:
                    real_value = read_result/100
                    publish_data(dset_name[i], dset_addr[i], real_value, 'Setting')
                    dset_old[i] = read_result

            except Exception as e:
                print('task_data_setting_process')
                print(e)
                reConEth_flg.set()


def task_data_count_process():
    list_totalHeight = ['S8_TOTAL_HEIGHT_TR1', 'S8_TOTAL_HEIGHT_TR3', 'S9_TOTAL_HEIGHT_TR2', 'S9_TOTAL_HEIGHT_TR4']
    while True:
        for i in range(dcount_length):
            time.sleep(0.001)
            t2_interupt.wait()
            try:
                _, read_result = plc.readData(dcount_addr[i], dcount_type[i])
                read_result = int(read_result)
                if dcount_old[i] != read_result:
                    if dcount_name[i] == 'goodProduct':
                        continue
                    # elif dcount_name[i] == 'EFF':
                    #     real_value =  read_result/10 
                    elif dcount_name[i] in list_totalHeight:
                        real_value = read_result/100
                    else:
                        real_value = read_result

                    publish_data(dcount_name[i], dcount_addr[i], real_value, 'Counting')
                    dcount_old[i] = read_result
                        
            except Exception as e:
                print('task_data_count_process')
                print(e)
                reConEth_flg.set()


def task_publish_operationTime():
    global old_operationTime, offset_operationTime
    while True:
        time.sleep(1)
        t10_interupt.wait()
        
        new_operationTime = datetime.now()
        delta_operationTime = (new_operationTime - old_operationTime + timedelta(seconds=offset_operationTime)).total_seconds()
        _delta_operationTime = (datetime.fromtimestamp(delta_operationTime) + timedelta(hours=-7)).strftime('%H:%M:%S')
        publish_data('operationTimeRaw', 'operationTimeRaw', _delta_operationTime, 'Counting')
        with lock:
            with open(filepath + 'old_operationTime.txt', 'w+') as file:
                file.write(str(delta_operationTime))


def task_data_checking_process():
    while True:
        for i in range(dcheck_length):
            time.sleep(0.001)
            t3_interupt.wait()
            try: 
                _, read_result = plc.readData(dcheck_addr[i], dcheck_type[i])
                if dcheck_old[i] != read_result:
                    publish_data(dcheck_name[i], dcheck_addr[i], read_result, 'Checking')
                    dcheck_old[i] = read_result

            except Exception as e:
                print('task_data_checking_process')
                print(e)
                reConEth_flg.set()


def task_data_alarm_process():
    while True:
        for i in range(dalarm_length):
            time.sleep(0.001)
            t5_interupt.wait()
            try: 
                _, read_result = plc.readData(dalarm_addr[i], dalarm_type[i])
                if dalarm_old[i] != read_result:
                    publish_data(dalarm_name[i], dalarm_addr[i], read_result, 'Alarm')
                    dalarm_old[i] = read_result

            except Exception as e:
                print('task_data_alarm_process')
                print(e)
                reConEth_flg.set()


def task_machineStatus_process():
    '''
    M1	    MANUAL MODE
    M0	    AUTO ON
    M65	    BF JAM FLT
    M3	    FLT FLG
    Y4	    INDEX MOTOR ON
    TS10	M/C IDLE TIME 
    SM400	Always ON
    '''
    global runStTimestamp
    status_new = -1
    # Each element in list_status_addr represents a specific address in the PLC, following the order of the alphabet.
    B = PLC_Mitsu.DictAsAttributes(list_status_addr)
    equ1 = f'{B.M0}.{B.Y4}.(/{B.M3}).(/{B.TS10})'
    equ2 = f'{B.TS10}.(/{B.Y4}).(/{B.M3})'
    equ3 = f'{B.M3}'
    equ4 = f'{B.M1}.{B.Y4}.(/{B.M3}).(/{B.TS10})'
    equ5 = f'{B.SM400}'

    while True:
        try:
            bits = plc.read_multiple_incoherent_bits(list_status_addr)
            time.sleep(0.001)
            if plc.checkLogicBits(bits, equ5):
                if plc.checkLogicBits(bits, equ1):
                    status_new = ST.Run
                    if ST.status_old != status_new:
                        publish_data('machineStatus', status_new, status_new, 'MachineStatus')
                        ST.status_old = status_new

                        if init.Run and not ST.is_connectWifi:
                            timestamp = datetime.now().isoformat(timespec='microseconds')
                            runStTimestamp = generate_general_data('machineStatus', ST.Run, timestamp)
                            init.Run = 0

                elif plc.checkLogicBits(bits, equ2) and ST.status_old!=ST.Setup and ST.status_old!=ST.On:
                    status_new = ST.Idle
                    if ST.status_old != status_new:
                        publish_data('machineStatus', status_new, status_new, 'MachineStatus')
                        ST.status_old = status_new

                elif plc.checkLogicBits(bits, equ3):
                    status_new = ST.Alarm
                    if ST.status_old != status_new:
                        publish_data('machineStatus', status_new, status_new, 'MachineStatus')
                        ST.status_old = status_new

                elif plc.checkLogicBits(bits, equ4):
                    status_new = ST.Setup
                    if ST.status_old != status_new:
                        publish_data('machineStatus', status_new, status_new, 'MachineStatus')
                        ST.status_old = status_new

        except Exception as e:
            print('task_machineStatus_process')
            print(e)
            reConEth_flg.set()


def task_reconnect_ethernetPLC():
    while True:
        lsname = []
        lsPayload = []

        reConEth_flg.wait()
        print('PLC disconnect!')

        clear_all_taskInterrupt()

        publish_data('machineStatus', ST.Ethernet_disconnect, ST.Ethernet_disconnect, 'MachineStatus')

        lsname, lsPayload = Log.get_data_disconnected_wifi()
        if lsname is not None:
            for i in range(len(lsname)):
                client.publish_data(lsname[i], lsPayload[i], is_payload=True)
            lsname.clear()
            lsPayload.clear()

        alwaysOn = 'SM400'
        # Wait for PLC to reconnect
        plc.reconnect(alwaysOn)
        
        publish_data('machineStatus', ST.status_old, ST.status_old, 'MachineStatus')
        reConEth_flg.clear()

        set_all_taskInterrupt()

#---------------------------------------------------------------------------
if __name__ == '__main__':
    
    t1 = threading.Thread(target=task_data_setting_process)
    t2 = threading.Thread(target=task_data_count_process)
    t3 = threading.Thread(target=task_data_checking_process)
    t4 = threading.Thread(target=task_data_alarm_process)
    t5 = threading.Thread(target=task_machineStatus_process)
    t6 = threading.Thread(target=task_publish_operationTime)
    task_reconnect_ehtPLC = threading.Thread(target=task_reconnect_ethernetPLC)

    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    task_reconnect_ehtPLC.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    task_reconnect_ehtPLC.join()

