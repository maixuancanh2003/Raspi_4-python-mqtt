"""
This file contains the functions to generate the json payload for the data to be sent to the cloud.

Library: json
Installation: pip install json
Information: This library supports json format.
"""

from datetime import datetime   
import json


def generate_data_status(state, value):
	"""
	Generate the json payload for the machine status data.
	"""
	data = [{
                'name': 'machineStatus',
                'value': value,
                'timestamp': datetime.now().isoformat(timespec='microseconds')
	}]
	return (json.dumps(data))


def generate_data(data_name, data_value):
	"""
	Generate the json payload for the machine data.
	"""
	data = [{
                'name': str(data_name),
                'value': data_value,
                'timestamp': datetime.now().isoformat(timespec='microseconds')
	}]
	return (json.dumps(data))


def generate_general_data(data_name, data_value, timestamp):
	data = [{
                'name': str(data_name),
                'value': data_value,
                'timestamp': timestamp
	}]
	return (json.dumps(data))
