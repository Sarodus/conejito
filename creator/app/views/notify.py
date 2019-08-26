import logging
from time import sleep

from flask import Blueprint, request

notify = Blueprint('notify', 'notify')


@notify.route('/notify/<path:star>', methods=['POST'])
def index(star):
    sleep(1)
    logging.warning('GOT NOTIFICATION! %s' % request.form)
    return 'OC'
