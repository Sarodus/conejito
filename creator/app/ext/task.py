#!/usr/bin/env python

import pika
import sys
from json import dumps


class Task(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.config = app.config
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.config['TASK_HOST'])
        )
        self.channel = self.connection.channel()

    def send(self, queue, routing_key, body, exchange='creator', durable=True, properties=None):
        self.channel.queue_declare(queue=queue, durable=durable)
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=dumps(body),
            properties=properties or pika.BasicProperties(
                delivery_mode=2,  # make message persistent
        ))
