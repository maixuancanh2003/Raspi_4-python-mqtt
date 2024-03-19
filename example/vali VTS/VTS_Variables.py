from fablab_lib import LogFileCSV

is_pc = 1
if not is_pc:
    filePath = '/home/pi/'
else:
    filePath = 'home/pi/VTS/'
fileName = 'stored_data.csv' 

Log = LogFileCSV(filePath, fileName)


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

# --------------------- User variable --------------------------------------

var_list = ['ns=4;i=7', 'ns=4;i=6', 'ns=4;i=8', 'ns=4;i=14', 'ns=4;i=15', 'ns=4;i=16', 'ns=4;i=12', 'ns=4;i=13', 
            'ns=4;i=47', 'ns=4;i=46', 'ns=4;i=48', 'ns=4;i=49', 'ns=4;i=32', 'ns=4;i=33', 'ns=4;i=35', 'ns=4;i=34', 
            'ns=4;i=28', 'ns=4;i=25', 'ns=4;i=26', 'ns=4;i=27', 'ns=4;i=21', 'ns=4;i=22', 'ns=4;i=24', 'ns=4;i=23', 
            'ns=4;i=40', 'ns=4;i=41', 'ns=4;i=42', 'ns=4;i=39']

name_list = [""]*len(var_list)
