import threading
from fablab_lib import LogFileCSV

# Check if the program is running on a PC or Raspberry Pi
is_pc = 1
if not is_pc:
    filepath = '/home/pi/MNC/'
else:
    # filepath = 'home/pi/'
    filepath = 'home/pi/MNC/'

# Log file for storing data
filename = 'stored_data.csv'
Log = LogFileCSV(fileName=filename, filePath=filepath)

# Variables to store machine states
class ST:
    On = 0                          # On state
    Run = 1                         # Running state
    Idle = 2                        # Idle state (no orders, machine is running but paused)
    Alarm = 3                       # Alarm state
    Setup = 4                       # Setup state (maintenance)
    Off = 5                         # Off state
    Ready = 6                       # Ready state (power on, not idle, not in fault)
    Wifi_disconnect = 7             # WiFi disconnect state
    Ethernet_disconnect = 8         # Ethernet disconnect state
    is_connectWifi = 0              # WiFi connect state
    status_old = -1                 # Old status

# Variables to store initial states
class init:
    On = 1                          # Initiate on state
    Run = 1                         # Initiate running state
    Idle = 1                        # Initiate idle state
    Alarm = 1                       # Initiate alarm state
    Setup = 1                       # Initiate setup state
    Off = 1                         # Initiate off state
    Ready = 1                       # Initiate ready state

lock = threading.Lock()  # Lock object for thread synchronization

reConEth_flg = threading.Event()  # Event flag for Ethernet reconnection

# Interrupt events for threads
t1_interupt = threading.Event()
t2_interupt = threading.Event()
t3_interupt = threading.Event()
t4_interupt = threading.Event()
t5_interupt = threading.Event()
t6_interupt = threading.Event()
t7_interupt = threading.Event()
t8_interupt = threading.Event()
t9_interupt = threading.Event()
t10_interupt = threading.Event()

def set_all_taskInterrupt():
    """Set all interrupt events"""
    t1_interupt.set()
    t2_interupt.set()
    t3_interupt.set()
    t4_interupt.set()
    t5_interupt.set()
    t6_interupt.set()
    t7_interupt.set()
    t8_interupt.set()
    t9_interupt.set()
    t10_interupt.set()

def clear_all_taskInterrupt():
    """Clear all interrupt events"""
    t1_interupt.clear()
    t2_interupt.clear()
    t3_interupt.clear()
    t4_interupt.clear()
    t5_interupt.clear()
    t6_interupt.clear()
    t7_interupt.clear()
    t8_interupt.clear()
    t9_interupt.clear()
    t10_interupt.clear()

# Set all interrupt events initially
set_all_taskInterrupt()


# Variables for setting values to determine whether the product meets the criteria or not
filename = 'setting_value.csv'
may_nut_chan_setting_value = LogFileCSV(fileName=filename, filePath=filepath)
dset_addr, dset_type, dset_name, dset_length, dset_old = may_nut_chan_setting_value.get_info_variable_from_csv(filepath, filename)

# Variables for counting good, bad, and efficiency
filename = 'counting_value.csv'
may_nut_chan_counting_value = LogFileCSV(fileName=filename, filePath=filepath)
dcount_addr, dcount_type, dcount_name, dcount_length, dcount_old = may_nut_chan_counting_value.get_info_variable_from_csv(filepath, filename)

# Variables for rejection details page
filename = 'checking_value.csv'
may_nut_chan_checking_value = LogFileCSV(fileName=filename, filePath=filepath)
dcheck_addr, dcheck_type, dcheck_name, dcheck_length, dcheck_old = may_nut_chan_checking_value.get_info_variable_from_csv(filepath, filename)

# Variables for alarm list displayed on HMI
filename = 'alarm_value.csv'
may_nut_chan_alarm_value = LogFileCSV(fileName=filename, filePath=filepath)
dalarm_addr, dalarm_type, dalarm_name, dalarm_length, dalarm_old = may_nut_chan_alarm_value.get_info_variable_from_csv(filepath, filename)


# Variables for alarm list displayed on HMI
'''
M1	    MANUAL MODE
M0	    AUTO ON
M170	ALL B/F FLT
M3	    FLT FLG
Y4	    INDEX MOTOR ON
T4	    M/C IDLE TD
M799    POWER ON

M0, Y4  	Run	    -->     M0.Y4./M170./M3./T4
M170, M3	Alarm	-->     (M170+M3)
T4	        Idle	-->     T4./Y4./M170./M3
M1, Y4  	Setup   -->     M1.Y4./M170./M3./T4
Y4 = 0	    Ready	-->     /Y4./T4./M170./M3
M799 = 0    Off     -->     /M799 hoặc khi code bị lỗi do ko thể giao tiếp với PLC        
M799 = 1    ON      -->     M799 

'''
list_status_addr = ['M1', 'M0', 'Y4', 'M170', 'M3', 'TS4', 'M799']
list_status_old = [0]*len(list_status_addr)

runStTimestamp = None
onStTimestamp = None

