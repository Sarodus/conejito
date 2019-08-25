import random
import string

from flask import Blueprint, render_template, request
from .extensions import task

main = Blueprint('main', 'main')


@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        queue = 'creator'
        routing_key, locator = get_random_action()
        body = {
            'locator': locator
        }
        print('SENT TASK', queue, routing_key, body)
        task.send(queue, routing_key, body)
    return render_template('index.html')


@main.route('/receive')
def receive():
    print('YOLO WHAAA Xd')
    return 'OC'

def get_random_action():
    method = random.choice(METHODS)
    locator = random.choice(LOCATORS)
    return method, locator


def generate_locators():
    locators = []
    for _ in range(random.randint(3, 10)):
        locators.append(
            ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
        )
    return locators

METHODS = (
    'booking.create',
    'booking.add_room',
    'booking.remove_room',
)

LOCATORS = generate_locators()
