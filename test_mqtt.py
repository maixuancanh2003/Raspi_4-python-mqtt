from fablab_lib import MQTT
import time
import threading
from fablab_lib import generate_data
import random
import string


standardTopic = 'TEST1/fablab/iot/'  # The standard topic for the MQTT broker
mqttBroker = '20.249.217.5'  # cloud
mqttPort = 1883
client1 = MQTT(host=mqttBroker, port=mqttPort)
client2 = MQTT(host=mqttBroker, port=mqttPort)
client3 = MQTT(host=mqttBroker, port=mqttPort)

client1.standardTopic = standardTopic
client2.standardTopic = standardTopic
client3.standardTopic = standardTopic


client1.connect()
client2.connect()
client3.connect()

def task1():
    while True:
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=30))
        client1.publish_data('task' + str(random.randint(1,3)), random_string)
        time.sleep(0.05)

def task2():
    while True:
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=25))
        client2.publish_data('task' + str(random.randint(4,6)), random_string)
        time.sleep(0.07)

def task3():
    while True:
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=35))
        client3.publish_data('task' + str(random.randint(7,9)), random_string)
        time.sleep(0.1)


if __name__ == '__main__':
    t1 = threading.Thread(target=task1)
    t2 = threading.Thread(target=task2)
    t3 = threading.Thread(target=task3)

    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()

    client1.disconnect()
    client2.disconnect()
    client3.disconnect()
