from fablab_lib import PLC_Mitsu, DT
from WB_P1_MBC_Variables import*

__HOST = '192.168.1.250' # REQUIRED
__PORT = 4096           # OPTIONAL: default is 5007
plc = PLC_Mitsu.PLC(host=__HOST, port=__PORT, nameStation='May_buong_chan', is_pc=is_pc)
plc.connect()