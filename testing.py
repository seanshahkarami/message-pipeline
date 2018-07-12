from waggle.protocol.v0 import *


def pack_message(message):
    if message['message_major_type'] == 0:
        return pack_sensor_data_message(message)


def pack_sensor_data_message(message):
    for datagram in message['body']:
        datagram['body']

# for now, publish assumes that we send
