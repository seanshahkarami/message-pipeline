#!/usr/bin/env python3
import pika
import secrets
from waggle.protocol.v0 import *

# WAGGLE_PLUGIN_CACERTFILE
# WAGGLE_PLUGIN_CERTFILE
# WAGGLE_PLUGIN_KEYFILE

class Plugin:

    def __init__(self, config):
        self.run_id = secrets.randbelow(0xffffffff)

        self.config = config
        self.queue = 'in-plugin-{}-{}-{}'.format(config['plugin_id'], config['plugin_major_version'], 0)

        credentials = pika.credentials.PlainCredentials(
            username=config.get('username', 'admin'),
            password=config.get('password', 'testing'))

        parameters = pika.ConnectionParameters(
            credentials=credentials)

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    def publish(self, body):
        datagram = pack_datagrams([{
            'plugin_id': self.config['plugin_id'],
            'body': body,
        }])

        self.channel.basic_publish('data', '', datagram)

    def get_waiting_messages(self):
        while True:
            method, properties, body = self.channel.basic_get(queue=self.queue)

            if method is None:
                return

            yield properties, body
            self.channel.basic_ack(delivery_tag=method.delivery_tag)
