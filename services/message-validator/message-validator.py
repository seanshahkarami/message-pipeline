#!/usr/bin/env python3
import argparse
import os
import pika
import re
from waggle.protocol.v0 import *


# these can become flags...otherwise, will attempt to autodetect
WAGGLE_NODE_ID = os.environ.get('WAGGLE_NODE_ID', '0000000000000000')
WAGGLE_DEVICE_ID = os.environ.get('WAGGLE_DEVICE_ID', '0000000000000000')


def parse_version_string(s):
    ver = tuple(map(int, s.split('.')))

    if len(ver) < 2:
        raise ValueError('Invalid version string.')

    return ver


def parse_plugin_user_id(user_id):
    match = re.match('plugin-([^-]+)-([^-]+)-([^-]+)', user_id)

    if match is None:
        raise ValueError('Invalid plugin user ID.')

    id_string, version_string, instance_string = match.groups()

    return {
        'id': int(id_string),
        'version': parse_version_string(version_string),
        'instance': int(instance_string),
    }


def stamp_message_headers(user_id, message_data):
    pass


def message_handler(ch, method, properties, body):
    print('---')
    user_id = properties.user_id

    if user_id is None:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print('Dropping message with missing user ID.', properties, body)
        return

    try:
        plugin_info = parse_plugin_user_id(user_id)
    except ValueError:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print('Dropping message with invalid plugin user ID.', properties, body)
        return

    packets = unpack_waggle_packets(body)

    for packet in packets:
        packet['sender_id'] = WAGGLE_NODE_ID
        packet['sender_sub_id'] = WAGGLE_DEVICE_ID

        datagrams = unpack_datagrams(packet['body'])

        for datagram in datagrams:
            datagram['plugin_id'] = plugin_info['id']
            datagram['plugin_major_version'] = plugin_info['version'][0]
            datagram['plugin_minor_version'] = plugin_info['version'][1]
            datagram['plugin_instance'] = plugin_info['instance']

        packet['body'] = pack_datagrams(datagrams)

    data = pack_waggle_packets(packets)

    ch.basic_publish(
      exchange='',
      routing_key='to-beehive',
      properties=pika.BasicProperties(
        delivery_mode=2),
      body=data)

    print('ok', user_id, data)

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='amqp://localhost', help='AMQP broker URL to connect to.')
    parser.add_argument('inqueue', help='Queue to consume from.')
    parser.add_argument('outqueue', help='Queue to publish to.')
    args = parser.parse_args()

    connection = pika.BlockingConnection(pika.URLParameters(args.url))
    channel = connection.channel()

    channel.queue_declare(queue=args.inqueue, durable=True)
    channel.queue_declare(queue=args.outqueue, durable=True)
    channel.basic_consume(message_handler, args.inqueue)
    channel.start_consuming()


if __name__ == '__main__':
    main()
