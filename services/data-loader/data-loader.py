#!/usr/bin/env python3
import argparse
import pika
import waggle.protocol.v0 as protocol


def message_handler(ch, method, properties, body):
    for message in protocol.unpack_waggle_packets(body):
        print('--- message')
        print(message)
        for datagram in protocol.unpack_datagrams(message['body']):
            print('--- datagram')
            print(datagram)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('node_id')
    args = parser.parse_args()

    queue = 'to-node-{}'.format(args.node_id)

    connection = pika.BlockingConnection(pika.URLParameters(args.url))
    channel = connection.channel()

    channel.queue_declare(queue=queue, durable=True)
    channel.basic_consume(message_handler, queue)
    channel.start_consuming()


if __name__ == '__main__':
    main()
