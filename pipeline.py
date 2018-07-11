#!/usr/bin/env python3
import logging
import os
import re
import pika
import secrets
from waggle.protocol.v0 import *


def parse_version_string(s):
    match = re.match('(\d+)\.(\d+)\.(\d+)', s)

    if match is None:
        raise ValueError('Invalid version string.')

    return tuple(int(x) for x in match.groups())


class Plugin:

    def __init__(self):
        self.logger = logging.getLogger('pipeline.Plugin')

        self.plugin_id = os.environ.get('WAGGLE_PLUGIN_ID', 0)
        self.logger.debug('Plugin ID is %s.', self.plugin_id)

        self.plugin_instance = os.environ.get('WAGGLE_PLUGIN_INSTANCE', 0)
        self.logger.debug('Plugin instance is %s.', self.plugin_instance)

        self.plugin_version = parse_version_string(os.environ.get('WAGGLE_PLUGIN_VERSION', '0.0.0'))
        self.logger.debug('Plugin version is %s.', self.plugin_version)

        self.plugin_token = os.environ.get('WAGGLE_PLUGIN_TOKEN', '')
        self.logger.debug('Plugin token is %s.', self.plugin_token)

        self.run_id = secrets.randbelow(0xffffffff)
        self.logger.debug('Plugin run ID is %s.', self.run_id)

        # self.queue = 'in-plugin-{}-{}-{}'.format(self.plugin_id, self.plugin_version[0], 0)
        #

        self.user_id = 'plugin_{}_{}_{}'.format(self.plugin_id, self.plugin_version[0], self.plugin_instance)

        credentials = pika.credentials.PlainCredentials(
            username=self.user_id,
            password=self.plugin_token)

        parameters = pika.ConnectionParameters(
            credentials=credentials,
            virtual_host='node1')

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        # self.channel.queue_declare(self.queue, durable=True)

    def publish(self, body):
        self.logger.debug('Publishing body %s', body)

        properties = pika.BasicProperties(
            delivery_mode=2,
            user_id=self.user_id)

        self.channel.basic_publish(
            exchange='',
            routing_key='data',
            body=body,
            properties=properties)

    def get_waiting_messages(self):
        while True:
            method, properties, body = self.channel.basic_get(queue=self.queue)

            if body is None:
                break

            try:
                datagrams = unpack_datagrams(body)
            except ValueError:
                print('invalid datagrams received')
                continue

            for datagram in datagrams:
                yield datagram

            self.channel.basic_ack(delivery_tag=method.delivery_tag)
