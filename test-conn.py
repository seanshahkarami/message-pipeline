import pika

parameters = pika.URLParameters('amqp://plugin-1-0.0.1-0:EZ-UN3PiSpaN3DrkbEXTcx_-U544Xxn9CTQdbN2WNmQ@localhost/node1')
connection = pika.BlockingConnection(parameters)
channel = connection.channel()


def message_handler(ch, method, properties, body):
    print(properties, body)
    ch.basic_ack(delivery_tag=method.delivery_tag)

queue = 'in-plugin-1-0.0.1-0'

channel.queue_declare(
  queue=queue,
  durable=True)

channel.basic_consume(message_handler, queue)
channel.start_consuming()
