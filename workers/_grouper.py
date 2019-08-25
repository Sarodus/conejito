#!/usr/bin/env python
import pika
import sys
from json import loads

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='conejito'))
channel = connection.channel()

channel.exchange_declare(exchange='creator', exchange_type='fanout')

result = channel.queue_declare('grouper', exclusive=True)
queue_name = result.method.queue

channel.queue_bind(
    exchange='creator',
    queue='grouper',
    routing_key=''
)

print(' [*] Waiting for messages. To exit press CTRL+C')


def callback(ch, method, properties, body):
    data = loads(body)
    print(" [x] %r:%r" % (method.routing_key, data))


channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback,
    auto_ack=True
)

channel.start_consuming()
