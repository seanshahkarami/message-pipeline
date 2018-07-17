#!/usr/bin/env python3
import argparse
from collections import defaultdict
import pika
import sqlite3
from waggle.protocol.v0 import pack_waggle_packets
from waggle.protocol.v0 import unpack_waggle_packets


class Router:

    def __init__(self, routing_table):
        self.routing_table = routing_table

    def route_message_data(self, message_data):
        routes = defaultdict(list)

        for message in unpack_waggle_packets(message_data):
            if not self.routing_table.is_message_routable(message):
                print('dropping', message, flush=True)
                continue

            route = self.routing_table.get_message_route(message)
            routes[route].append(message)

        for route, messages in routes.items():
            print('routing', messages, route, flush=True)
            yield pack_waggle_packets(messages), route


class MockRoutingTable:

    def __init__(self, rules):
        self.rules = rules

    def is_message_routable(self, message):
        if self.rules is True:
            return True
        if self.rules is False:
            return False
        raise NotImplementedError('General rules not implemented yet.')

    def get_message_route(self, message):
        return 'to-node-{}'.format(message['receiver_id'].decode())


class SqliteRoutingTable:

    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)

    def is_message_routable(self, message):
        return False

    def get_message_route(self, message):
        return 'to-node-{}'.format(message['receiver_id'].decode())


class NodeRoutingTable:

    def is_message_routable(self, message):
        return True

    def get_message_route(self, message):
        return 'to-device-{}'.format(message['receiver_sub_id'].decode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='amqp://localhost', help='AMQP broker URL to connect to.')
    parser.add_argument('queue', help='Message queue to process.')
    args = parser.parse_args()

    parameters = pika.URLParameters(args.url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=args.queue, durable=True)

    router = Router(MockRoutingTable())

    def message_handler(ch, method, properties, body):
        print('processing message data', flush=True)

        for data, queue in router.route_message_data(body):
            ch.queue_declare(queue=queue, durable=True)
            ch.basic_publish(exchange='', routing_key=queue, body=data)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(message_handler, args.queue)
    channel.start_consuming()


if __name__ == '__main__':
    main()
