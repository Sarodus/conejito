#!/usr/bin/env python

import pika
import sys
import logging
from json import dumps


class Task(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.config = app.config
        self.connect()

    def connect(self):
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
        try:
            self.channel.basic_publish(
                exchange='creator',
                routing_key=routing_key,
                body=dumps(body).encode(),
            )
        except Exception as e:
            logging.error('ERRRR %s, trying to reconnect...' % e)
            self.connect()
            self.send(queue, routing_key, body)
