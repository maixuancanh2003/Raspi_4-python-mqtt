
"""
This module provides a class for interacting with the E5CC temperature controller device.
"""

import struct
import time
import serial
import logging

# Application logger
logger = logging.getLogger("E5CC")
logger.setLevel(logging.DEBUG)
_log_handle = logging.StreamHandler()
_log_handle.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s | %(message)s'))
logger.addHandler(_log_handle)


class E5CC:
    def __init__(
            self,
            port='/dev/serial0',    
            baudrate=9600,
            parity=serial.PARITY_EVEN,
            timeout=1
        ):
        """
        Initialize the E5CC temperature controller object.

        :param port: the serial port to communicate with the device (default: '/dev/serial0')
        :param baudrate: the baud rate for serial communication (default: 9600)
        :param parity: the parity setting for serial communication (default: serial.PARITY_EVEN)
        :param timeout: the timeout value for serial communication (default: 1)
        """
        self.ser = serial.Serial(
            # port='/dev/serial0',      # module RS485 thường on RPi
            # port='/dev/ttyUSB0',      # module RS485 USB on RPi
            # port='COM3',              # module RS485 USB on Windows
            # port='/dev/ttyAMA0',
            port=port,
            baudrate=baudrate,
            parity=parity,
            timeout=timeout
        )
        

    def read_temp_value(self, type_value, device_id):
        """
        Read temperature value from the device.

        :param type_value: the type of value to read ('PV' for process value, 'SP' for set point)
        :param device_id: the ID of the device
        :return: the temperature value in Celsius
        """
        # Read holding register function code
        function_code = 3
        # Start address for temperature PV/SP value
        if type_value == "PV":
            start_address = 0       # read process value
        elif type_value == "SP":
            start_address = 262     # read set point
        else:
            logger.error("Invalid type value")
            return
        # Number of registers to read
        register_count = 2
        # Calculate Modbus RTU message
        message = bytearray([device_id, function_code, start_address >> 8, start_address & 0xff,
                            register_count >> 8, register_count & 0xff])
        # Calculate CRC
        crc = 0xFFFF
        for i in range(len(message)):
            crc = crc ^ message[i]
            for j in range(8):
                if (crc & 0x0001) != 0:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1
        # Append CRC to message
        message.append(crc & 0xff)
        message.append(crc >> 8)
        # Write message to serial port
        self.ser.write(message)
        time.sleep(0.2)
        response = self.ser.read(9)
        # Check response length and validity of CRC
        if len(response) != 9:
            return None
        else:
            crc = 0xFFFF
            for i in range(len(response) - 2):
                crc = crc ^ response[i]
                for j in range(8):
                    if (crc & 0x0001) != 0:
                        crc = (crc >> 1) ^ 0xA001
                    else:
                        crc = crc >> 1
            # Check if calculated CRC matches the received CRC
            if crc != (response[-1] << 8 | response[-2]):
                logger.error("CRC check failed")
                return None
            else:
                # Return the temperature value in Celsius
                address, function_code, byte_count, temperature_value = struct.unpack('!BBBl', response[:7])
                return temperature_value / 10
