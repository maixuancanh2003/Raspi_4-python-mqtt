from fablab_lib import LogFileCSV
import threading

# Check if the program is running on a PC or Raspberry Pi
is_pc = 1
if not is_pc:
    filepath = '/home/pi/ClotaActivator/'
else:
    filepath = 'home/pi/OMCK/ClotActivator/'

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

# Log file for storing data
filename = 'stored_data.csv'
Log = LogFileCSV(fileName=filename, filePath=filepath)

# Variables for counting values of machine
filename = 'counting_value.csv'
clot_activator_counting_value = LogFileCSV(fileName=filename, filePath=filepath)
dcount_addr, dcount_type, dcount_name, dcount_lenght, dcount_old = clot_activator_counting_value.get_info_variable_from_csv(filepath, filename)

# Variables for signal values of machine    
filename = 'signal_value.csv'
clot_activator_signal_value = LogFileCSV(fileName=filename, filePath=filepath)
dsignal_addr, dsignal_type, dsignal_name, dsignal_lenght, dsignal_old = clot_activator_signal_value.get_info_variable_from_csv(filepath, filename)

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