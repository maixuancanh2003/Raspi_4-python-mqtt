"""
This file contains the implementation of the LogFileCSV class, which is responsible for logging data to a CSV file.
"""

from fablab_lib.Broker.JsonPayload.function import*
from datetime import datetime
import logging
import os
import threading
import pandas as pd

lock = threading.Lock() # Lock to prevent multiple threads from writing to the same file at the same time

# Application logger
logger = logging.getLogger("LogFileCSV")
logger.setLevel(logging.DEBUG)
_log_handle = logging.StreamHandler()
_log_handle.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s | %(message)s'))
logger.addHandler(_log_handle)


class LogFileCSV:
    def __init__(self, filePath: str, fileName: str):
        """
        Initializes a LogFileCSV object.

        Args:
            filePath (str): The path to the directory where the log file will be stored.
            fileName (str): The name of the log file.

        Raises:
            FileNotFoundError: If the specified log file does not exist, it will be created.
        """
        self.filePath = filePath
        self.fileName = fileName
        self.No = 0
        try:
            with open(self.filePath + self.fileName) as store_data:
                pass
            logger.info('File {0} is already existed.'.format(fileName))
        except FileNotFoundError:
            with open(self.filePath + self.fileName, 'w+') as store_data:
                store_data.write('{0},{1},{2},{3},{4},{5},{6}\n'.format('No.','VarAddr','VarName','VarValue','Timestamp','KindofData','is_ConnectedWifi'))
            logger.info('File {0} is created.'.format(fileName))


    def get_info_variable_from_csv(self, filePath: str, fileName: str):
        """
        Retrieves information of variables from the CSV file using pandas.
        
        Args:
            filePath (str): The path to the directory where the log file is stored.
            fileName (str): The name of the log file.
            
        Returns:
            tuple: A tuple containing five lists: data_addr (list of addresses), data_type (list of data types), data_name (list of names), 
            data_length (length of data), and data_old (list of old values).
        """
        # Read data from CSV file
        data_frame = pd.read_csv(filePath + fileName, index_col=0)
        # Get header from CSV file
        headers = data_frame.columns.tolist()
        # print(headers)

        for header in headers:
            if 'ID' in header:
                data_addr = [*data_frame[header]]
            elif 'Type' in header:
                data_type = [*data_frame[header]]
            elif 'Name' in header:
                data_name = [name.strip() for name in [*data_frame[header]]]
        
        data_length = len(data_addr)
        data_old = [-1] * data_length

        logger.info(f'Completed reading data from CSV file {filePath+fileName}!')
        return data_addr, data_type, data_name, data_length, data_old


    def log_data(self, 
            VarName: str, 
            VarAddr: str, 
            VarValue, 
            KindOfData: str, #'setting', 'counting', 'checking', 'alarm'
            is_ConnectedWifi: bool=True
            ):
        """
        Logs data to the CSV file.

        Args:
            VarName (str): The name of the variable.
            VarAddr (str): The address of the variable.
            VarValue: The value of the variable.
            KindOfData (str): The kind of data. Can be 'setting', 'counting', 'checking', or 'alarm'.
            is_ConnectedWifi (bool, optional): Indicates whether the device is connected to Wi-Fi. Defaults to True.
        """
        Timestamp = datetime.now().isoformat(timespec='microseconds')
        with lock:
            with open(self.filePath + self.fileName, 'a+') as store_data:
                store_data.write('{0},{1},{2},{3},{4},{5},{6}\n'.format(self.No, 
                                                                    VarAddr, 
                                                                    VarName, 
                                                                    VarValue, 
                                                                    Timestamp, 
                                                                    KindOfData, 
                                                                    int(is_ConnectedWifi)))
            
        if not is_ConnectedWifi: # Store data when the device is disconnected from Wi-Fi
            data = generate_data(VarName, VarValue)
            with lock:
                with open(self.filePath + 'stored_disconnectWifi_data.txt', 'a+') as file:
                    file.write(str(data) + '\n')
            logger.info(f'Disconnected Wifi -> Log: {data}')
        self.No += 1


    def get_data_disconnected_wifi(self):
        """
        Retrieves the stored messages from the file when the device is disconnected from Wi-Fi.

        Returns:
            tuple: A tuple containing two lists: lsName (list of names) and lsPayload (list of payloads).
        """
        ls_name = []
        ls_payload = []
        try:
            with lock:
                with open(self.filePath + 'stored_disconnectWifi_data.txt') as file:
                    messages = file.read().splitlines()

            for message in messages:
                _message = json.loads(message.replace('\\','').replace('[','').replace(']',''))
                ls_name.append(_message['name'])
                ls_payload.append(message.replace('\\',''))

            logger.info('Completed reading stored messages!')
            # Clear the file
            myfile = self.filePath + 'stored_disconnectWifi_data.txt'
            if os.path.isfile(myfile):
                os.remove(myfile)
                logger.info('Cleared stored messages!')

        except FileNotFoundError:
            logger.info('No stored messages!')

        return ls_name, ls_payload


