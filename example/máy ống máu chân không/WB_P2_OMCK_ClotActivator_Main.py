from WB_P2_OMCK_ClotActivator_Variables import*
from WB_P2_OMCK_ClotActivator_PLC import*
from WB_P2_OMCK_ClotActivator_MQTT import*

# --------------------------- Tasks -------------------------------------
def task_data_count_process():
	while True:
		for i in range(dcount_lenght):
			time.sleep(0.01)
			try:
				_, value = plc_ClotActivator.readData(dcount_addr[i])
				if dcount_old[i] != value:
					publish_data(dcount_name[i], dcount_addr[i], value, 'Counting')
					dcount_old[i] = value
						
			except Exception as e:
				print('task_data_count_process')
				print(e)
				reConEth_flg.set()


def task_data_signal_process():
	while True:
		for i in range(dsignal_lenght):
			time.sleep(0.01)
			try:
				value = plc_ClotActivator.readData(dsignal_addr[i])
				if dsignal_old[i] != value:
					publish_data(dsignal_name[i], dsignal_addr[i], value, 'Signal')
					dsignal_old[i] = value
						
			except Exception as e:
				print('task_data_signal_process')
				print(e)
				reConEth_flg.set()


def task_reconnect_ethernetPLC():
	while True:	
		lsname = []
		lsPayload = []

		reConEth_flg.wait()

		clear_all_taskInterrupt()

		print('PLC disconnect!')
		publish_data('machineStatus', ST.Ethernet_disconnect, ST.Ethernet_disconnect, 'MachineStatus')

		lsname, lsPayload = Log.get_data_disconnected_wifi()
		if lsname is not None:
			for i in range(len(lsname)):
				client.publish_data(lsname[i], lsPayload[i], is_payload=True)
			lsname.clear()
			lsPayload.clear()

		alwaysOn = 'VX200.1'
		# Wait for PLC to reconnect
		plc_ClotActivator.reconnect(alwaysOn)

		publish_data('machineStatus', ST.status_old, ST.status_old, 'MachineStatus')
		reConEth_flg.clear()

		set_all_taskInterrupt()


#---------------------------------------------------------------------------

if __name__ == '__main__':
    
	t1 = threading.Thread(target=task_data_count_process)
	t2 = threading.Thread(target=task_data_signal_process)
	t3 = threading.Thread(target=task_reconnect_ethernetPLC)

	t1.start()
	t2.start()
	t3.start()

	t1.join()
	t2.join()
	t3.join()