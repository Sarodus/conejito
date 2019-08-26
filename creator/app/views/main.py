import random
import string
import logging

from flask import Blueprint, render_template, request
from ..extensions import task

main = Blueprint('main', 'main')

METHODS = (
    'booking.create',
    'booking.modify.add_room',
    'booking.modify.remove_room',
    'booking.cancel',
)

@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        routing_key = request.json['action']
        queue = 'creator'
        locator = get_random_locator()
        body = {
            'locator': locator
        }
        logging.info('SENT TASK', queue, routing_key, body)
        task.send(queue, routing_key, body)
    return render_template('index.html', METHODS=METHODS)


def get_random_locator():
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
