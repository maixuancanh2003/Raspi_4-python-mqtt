from fablab_lib import restart_program
from OMvsHT_VARs import*
from OMvsHT_Spb import*
from OMvsHT_FINS import*
from OMvsHT_OPCUA import*
import subprocess
# import RPi.GPIO as GPIO

PinReset = 4

#--------------------------- Functions --------------------------------
# def setup_pin(): # Setup pin for reset program
#     global PinReset, htStartESP
#     GPIO.setmode(GPIO.BCM)
#     GPIO.setup(PinReset, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#     GPIO.setup(htStartESP, GPIO.OUT, initial=GPIO.LOW)


#------------------------------ Tasks ------------------------------------
def task_wifi_disconnect():
    count = 0
    while True:
        wifi_disconnect_flag.wait()
        while not ip_PLC.is_connect_wifi:
            time.sleep(1)
            count += 1
            print(count)
            if count == 500:
                restart_raspberry()
        count = 0
        wifi_disconnect_flag.clear()


def is_ethernet_connected(ip_address):
    try:
        ping_command = ["ping", "-c", "1", str(ip_address)]
        ping_process = subprocess.Popen(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return_code = ping_process.wait()
        if return_code == 0:
            return True
        else:
            return False
        
    except subprocess.CalledProcessError as e:
        # Handle subprocess errors if needed
        print(f"Error running ping command: {e}")
        return False


def task_detect_disconnectPLC():
    omPLC_connected_flag.wait()
    htPLC_connected_flag.wait()

    htOldRes = -1
    omOldRes = -1

    countDisconnect = 0
    while True:
        res = is_ethernet_connected(ip_PLC.htIPEthernet)
        # print(res)
        if res == True and htOldRes != res:
            htOldRes = res
            print("Connected to PLC Siemens!")
        elif res != True and htOldRes != res:
            htOldRes = res
            countDisconnect += 1
            print(countDisconnect)
            print("Disconnected to PLC Siemens!")
            htReconnectPLC_flag.set()
        time.sleep(2)

        res = is_ethernet_connected(ip_PLC.omIPEthernet)
        # print(res)
        if res == True and omOldRes != res:
            omOldRes = res
            print("Connected to PLC Omron!")
        elif res != True and omOldRes != res:
            omOldRes = res
            countDisconnect += 1
            print(countDisconnect)
            print("Disconnected to PLC Omron!")
            omReconnectPLC_flag.set()
        time.sleep(2)

        if countDisconnect == 500:
            print('Reset Program!')
            restart_program()


# def checkButton():
#     global PinReset, htStartESP
#     try:
#         while True:
#             threading.Event().wait(0.1)
#             if(GPIO.input(PinReset)==0):
#                 threading.Event().wait(0.1)
#                 while(GPIO.input(PinReset)==0):
#                     threading.Event().wait(0.05)
#                 threading.Event().wait(0.1)

#                 omResetProgramOMRON()
#                 htResetProgramSIEMENS()
                
#                 GPIO.output(htStartESP, GPIO.HIGH)
#                 time.sleep(1)
#                 GPIO.output(htStartESP, GPIO.LOW)
#     except Exception as e:
#         print(e)
#         htReconnectPLC_flag.set()
#         omReconnectPLC_flag.set()

################################ OMRON ###################################
def task_omReconnectPLC():
    while True:
        omReconnectPLC_flag.wait()
        om1_flag.clear()
        om2_flag.clear()
        with lock:
            omDevice.Publish_Death(1)
            Log.log_data('DEATH', None, 'N03/DV01', 'Omron', ip_PLC.is_connect_wifi)

        count = 0
        while True:
            res = is_ethernet_connected(ip_PLC.omIPEthernet)
            time.sleep(1)
            if res:
                print("Connected to the ip")
                break
            else:
                print("No FINS connection.")
                if count==10:
                    count=0
                count+=1
                print(count)

        print('FINS connected!')

        omDevice.Publish_Death(0)
        omRebirth_flag.set()
        om1_flag.set()
        om2_flag.set()

        omReconnectPLC_flag.clear()
        # restart_program()

################################ HAITHIEN ###################################
def task_htReconnectPLC():
    while True:
        htReconnectPLC_flag.wait()
        ht1_flag.clear()
        ht2_flag.clear()
        is_already_published = 0

        count=0
        while True:
            res = is_ethernet_connected(ip_PLC.htIPEthernet)
            time.sleep(1)
            if res:
                print("Connected to the ip")
                break
            else:
                print("No opcua connection.")
                if not is_already_published:
                    htDevice.Publish_Death(1)
                    Log.log_data('DEATH', None, 'N02/DV01', 'Siemens', ip_PLC.is_connect_wifi)
                    is_already_published = 1

                if count==10:
                    count=0
                count+=1
                print(count)
            
        print("ua client connected")

        htDevice.Publish_Death(0)
        htRebirth_flag.set()
        ht1_flag.set()
        ht2_flag.set()

        htReconnectPLC_flag.clear()

##########################################################################

#------------------------------ Main -------------------------------------

if __name__ == '__main__':
    # setup_pin()

    tWifi = threading.Thread(target=task_wifi_disconnect)
    tDetectEthernet = threading.Thread(target=task_detect_disconnectPLC)
    # tCheckButton = threading.Thread(target=checkButton)

    omT1 = threading.Thread(target=task_omRead_data_plc)
    omT2 = threading.Thread(target=task_omCount_cycleTime)
    omT3 = threading.Thread(target=task_omRebirth)
    omT4 = threading.Thread(target=task_omCheckIP_PLC)
    omT5 = threading.Thread(target=task_omReconnectPLC)

    htT1 = threading.Thread(target=task_htRead_data_plc)
    # htT2 = threading.Thread(target=task_htSubcribe_node_opcua)
    htT3 = threading.Thread(target=task_htRebirth)
    htT4 = threading.Thread(target=task_htReconnectPLC)

    omT1.start()
    omT2.start()
    omT3.start()
    omT4.start()
    omT5.start()

    htT1.start()
    # htT2.start()
    htT3.start()
    htT4.start()

    # tCheckButton.start()
    tWifi.start()
    tDetectEthernet.start()
    
    omT1.join()
    omT2.join()
    omT3.join()
    omT4.join()
    omT5.join()

    htT1.join()
    # htT2.join()
    htT3.join()
    htT4.join()

    # tCheckButton.join()
    tWifi.join()
    tDetectEthernet.join()


            
