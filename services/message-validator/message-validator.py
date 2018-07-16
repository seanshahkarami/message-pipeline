#!/usr/bin/env python3
import argparse
import os
import pika
import re
from waggle.protocol.v0 import *


WAGGLE_NODE_ID = os.environ.get('WAGGLE_NODE_ID', '00000000').encode()
WAGGLE_DEVICE_ID = os.environ.get('WAGGLE_DEVICE_ID', '00000000').encode()


def parse_version_string(s):
    match = re.match(r'(\d+)\.(\d+)\.(\d+)', s)

    if match is None:
        return None

    return tuple(int(n) for n in match.groups())


def parse_plugin_user_id(user_id):
    match = re.match('plugin-([^-]+)-([^-]+)-([^-]+)', user_id)

    if match is None:
        raise ValueError('Invalid plugin user ID.')

    id_string, version_string, instance_string = match.groups()

    return {
        'id': int(id_string, 16),
        'version': parse_version_string(version_string),
        'instance': int(instance_string),
    }


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

    for packet in unpack_waggle_packets(body):
        for subpacket in unpack_datagrams(packet['body']):
            data = pack_waggle_packets([
                {
                    'sender_id': WAGGLE_NODE_ID,
                    'sender_sub_id': WAGGLE_DEVICE_ID,
                    'receiver_id': packet['receiver_id'],
                    'receiver_sub_id': packet['receiver_sub_id'],
                    'body': pack_datagrams([
                        {
                            'plugin_id': plugin_info['id'],
                            'plugin_major_version': plugin_info['version'][0],
                            'plugin_minor_version': plugin_info['version'][1],
                            'plugin_instance': plugin_info['instance'],
                            'body': subpacket['body'],
                        }
                    ])
                }
            ])

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
    parser.add_argument('url', help='AMQP broker URL to connect to.')
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
