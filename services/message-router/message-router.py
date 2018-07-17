#!/usr/bin/env python3
import argparse
import logging
import pika
from waggle.protocol.v0 import pack_waggle_packets, unpack_waggle_packets
from waggle.protocol.v0 import pack_datagrams, unpack_datagrams


class BeehiveRouter:

    def is_message_routable(self, message):
        return True

    def generate_message_routes(self, message_data):
        for message in unpack_waggle_packets(message_data):
            if not self.is_message_routable(message):
                logging.info('Dropping message %s.', message)
                continue

            route_data = pack_waggle_packets([message])
            route_name = 'to-node-{}'.format(message['receiver_sub_id'])
            yield route_data, route_name


class NodeRouter:

    def generate_message_routes(self, message_data):
        for message in unpack_waggle_packets(message_data):
            route_data = pack_waggle_packets([message])
            route_name = 'to-device-{}'.format(message['receiver_sub_id'])
            yield route_data, route_name


class PluginRouter:

    def generate_message_routes(self, message_data):
        for message in unpack_waggle_packets(message_data):
            for datagram in unpack_datagrams(message['body']):
                plugin_message = message.copy()
                plugin_message['body'] = pack_datagrams([datagram])

                route_data = pack_waggle_packets([plugin_message])

                route_name = 'to-plugin-{}-{}-{}'.format(
                    datagram['plugin_id'],
                    datagram['plugin_major_version'],
                    datagram['plugin_instance'])

                yield route_data, route_name


def setup_logging(args):
    if args.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S %Z',
        level=loglevel)


router_modes = {
    'beehive': BeehiveRouter,
    'node': NodeRouter,
    'plugin': PluginRouter,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--url', default='amqp://localhost', help='AMQP broker URL to connect to.')
    parser.add_argument('mode', help='Router mode. (beehive,node,plugin)')
    parser.add_argument('queue', help='Message queue to process.')
    args = parser.parse_args()

    setup_logging(args)

    parameters = pika.URLParameters(args.url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=args.queue, durable=True)

    router = router_modes[args.mode]()

    def message_handler(ch, method, properties, body):
        logging.info('Processing message data.')

        for data, queue in router.generate_message_routes(body):
            ch.queue_declare(queue=queue, durable=True)
            ch.basic_publish(exchange='', routing_key=queue, body=data)

        logging.info('Acking message data.')
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(message_handler, args.queue)
    channel.start_consuming()


if __name__ == '__main__':
    main()
