#!/usr/bin/env python3
import logging
import os
import re
import pika
import secrets
from waggle.protocol.v0 import *


class Plugin:

    def __init__(self, credentials=None):
        self.logger = logging.getLogger('pipeline.Plugin')

        if credentials is None:
            username, password = os.environ['WAGGLE_PLUGIN_CREDENTIALS'].split(':')
        else:
            username, password = credentials

        self.user_id = username
        self.run_id = secrets.randbelow(0xffffffff)
        self.queue = 'in-{}'.format(username)

        credentials = pika.credentials.PlainCredentials(
            username=username,
            password=password)

        parameters = pika.ConnectionParameters(
            credentials=credentials,
            virtual_host='node1')

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        self.channel.queue_declare(
            queue=self.queue,
            durable=True)

    def publish(self, body, receiver=None):
        self.logger.debug('Publishing body %s', body)

        if receiver is None:
            receiver = (b'00000000', b'00000000')

        packet = pack_waggle_packets([
            {
                'sender_id': b'00000000',
                'sender_sub_id': b'00000000',
                'receiver_id': receiver[0],
                'receiver_sub_id': receiver[1],
                'body': body,
            }
        ])

        self.channel.basic_publish(
            exchange='data',
            routing_key='',
            properties=pika.BasicProperties(
                delivery_mode=2,
                user_id=self.user_id),
            body=packet)

    def get_waiting_messages(self):
        while True:
            method, properties, body = self.channel.basic_get(queue=self.queue)

            if body is None:
                break

            try:
                messages = unpack_waggle_packets(body)
            except ValueError:
                self.channel.basic_ack(delivery_tag=method.delivery_tag)
                print('Dropping invalid packets.')
                continue

            for message in messages:
                yield message

            self.channel.basic_ack(delivery_tag=method.delivery_tag)
