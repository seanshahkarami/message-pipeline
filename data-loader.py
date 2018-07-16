import pika
from waggle.protocol.v0 import unpack_waggle_packets


def message_handler(ch, method, properties, body):
    for datagram in unpack_waggle_packets(body):
        print('---')
        print('saving datagram in db')
        print(datagram)
    ch.basic_ack(delivery_tag=method.delivery_tag)


queue = 'to-node-00000000'

url = 'amqp://admin:admin@localhost/node1'
connection = pika.BlockingConnection(pika.URLParameters(url))
channel = connection.channel()

channel.queue_declare(queue=queue, durable=True)
channel.basic_consume(message_handler, queue)
channel.start_consuming()
