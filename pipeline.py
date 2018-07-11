#!/usr/bin/env python3
import logging
import os
import re
import pika
import secrets
from waggle.protocol.v0 import *


class Plugin:

    def __init__(self, username=None, password=None):
        self.logger = logging.getLogger('pipeline.Plugin')

        if username is None:
            username = os.environ['WAGGLE_PLUGIN_USER']

        if password is None:
            password = os.environ['WAGGLE_PLUGIN_TOKEN']

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

    def publish(self, body):
        self.logger.debug('Publishing body %s', body)

        self.channel.basic_publish(
            exchange='data',
            routing_key='',
            properties=pika.BasicProperties(
                delivery_mode=2,
                user_id=self.user_id),
            body=body)

    def get_waiting_messages(self):
        while True:
            method, properties, body = self.channel.basic_get(queue=self.queue)

            if body is None:
                break

            try:
                datagrams = unpack_datagrams(body)
            except ValueError:
                self.channel.basic_ack(delivery_tag=method.delivery_tag)
                print('Dropping invalid datagrams.')
                continue

            for datagram in datagrams:
                yield datagram

            self.channel.basic_ack(delivery_tag=method.delivery_tag)
