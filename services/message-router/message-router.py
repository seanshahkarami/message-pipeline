#!/usr/bin/env python3
import argparse
from collections import defaultdict
import pika
from routing import MockRoutingTable
from waggle.protocol.v0 import pack_waggle_packets
from waggle.protocol.v0 import unpack_waggle_packets


routing_table = MockRoutingTable(True)


def process_waggle_messages(message_data):
    routes = defaultdict(list)

    for message in unpack_waggle_packets(message_data):
        if not routing_table.is_message_routable(message):
            print('dropping', message, flush=True)
            continue

        route = routing_table.get_message_route(message)
        routes[route].append(message)

    for route, messages in routes.items():
        print('routing', messages, route, flush=True)
        yield pack_waggle_packets(messages), route


def message_handler(ch, method, properties, body):
    print('processing message data', flush=True)

    for data, queue in process_waggle_messages(body):
        ch.queue_declare(queue=queue, durable=True)
        ch.basic_publish(exchange='', routing_key=queue, body=data)

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='AMQP broker URL to connect to.')
    parser.add_argument('queue', help='Message queue to process.')
    args = parser.parse_args()

    parameters = pika.URLParameters(args.url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=args.queue, durable=True)
    channel.basic_consume(message_handler, args.queue)
    channel.start_consuming()


if __name__ == '__main__':
    main()
