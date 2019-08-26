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
        self.channel.exchange_declare(
            exchange='creator',
            exchange_type='topic',
            auto_delete=False,
            durable=True
        )

    def send(self, queue, routing_key, body):
        self.channel.basic_publish(
            exchange='creator',
            routing_key=routing_key,
            body=dumps(body).encode(),
        #     properties=properties or pika.BasicProperties(
        #         delivery_mode=2,  # make message persistent
        # )
        )
