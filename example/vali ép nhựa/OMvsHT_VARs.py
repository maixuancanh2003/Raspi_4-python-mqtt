import threading
from fablab_lib import LogFileCSV

is_pc = 1
if not is_pc:
    filePath = '/home/pi/'
else:
    filePath = 'home/pi/OMvsHT/'
fileName = 'stored_newData.csv'

Log = LogFileCSV(filePath, fileName)

# --------------------- User variable - General ----------------------
lock = threading.Lock()
wifi_disconnect_flag = threading.Event()
omReconnectPLC_flag = threading.Event()
htReconnectPLC_flag = threading.Event()

om1_flag = threading.Event()
om2_flag = threading.Event()
om3_flag = threading.Event()
om4_flag = threading.Event()
ht1_flag = threading.Event()
ht2_flag = threading.Event()
ht3_flag = threading.Event()
ht4_flag = threading.Event()

om1_flag.set()
om2_flag.set()
om3_flag.set()
om4_flag.set()
ht1_flag.set()
ht2_flag.set()
ht3_flag.set()
ht4_flag.set()

# --------------------- User variable - OMRON ----------------------
omCheckIP_flag = threading.Event()
omRebirth_flag = threading.Event()
omFINS_flag = threading.Event()
omPLC_connected_flag = threading.Event()


'''
Real name of value from PLC:
    %Name Variable%	    %Address%
    temperature_SP	    b'\x01\x90\x00'
    temperature	        b'\x02\x58\x00'
    pressure_SP	        b'\x02\x0c\x00'
    pressure	        b'\x02\x08\x00'
    injectionTime	    b'\x00\x01\x06'
    cycleTime	        b'\x00\x02\x04'
    counterShot	        b'\x00\x02\x0A'
'''

omVar_fake = ['cycleTime', 'counterShot']
omVar_name = []
omVar_addr = []
omOld_var = []
#--------------------------------------------------------------------

# --------------------- User variable - HAITHIEN --------------------
htCheckIP_flag = threading.Event()
htRebirth_flag = threading.Event()
htOPCUA_flag = threading.Event()
htPLC_connected_flag = threading.Event()
htNodeSub_flag = threading.Event()
htSubscribing_flag = threading.Event()

htStartESP = 6

err_subNode = 0
'''
Real name of value from PLC:
    %Name Variable%	            %Address%
    tmChargeTime	            ns=4;i=9
    tmClpClsTime	            ns=4;i=10
    tmClpOpnTime	            ns=4;i=8
    tmCoolingTime	            ns=4;i=15
    tmInjTime	                ns=4;i=7
    Injection Peak Pressure	    ns=4;i=16
    cycleTime	                ns=4;i=14
    counterShot	                ns=4;i=12
    Nozzle Temp	                ns=4;i=11
    Switch Over Pos	            ns=4;i=13

'''
htVar_fake = []
htVar_name = []
htVar_addr = []
htOld_var = []
htList_sub = []
#-----------------------------------------------------------------------

class ip_PLC:
    omIPEthernet = ''
    htIPEthernet = '192.168.0.1'
    is_connect_wifi = 0

class Payload:
    omPayloadDevice = None
    omPayloadNode = None    
    htPayloadDevice = None
    htPayloadNode = None

class bitReset:
    om = b'\x00\x00\x00'
    ht = 'ns=4;i=17'

class init:
    htSub = 1

