import logging
import asyncio
import json
from time import sleep

from sanic import Blueprint, request
from sanic.response import text
from sanic.websocket import ConnectionClosed

notify = Blueprint('notify')


@notify.route('/notify/<action:string>', methods=['POST'])
async def index(request, action):
    logging.warning('GOT NOTIFICATION! %s - %s' % (action, request.form))
    await broadcast(request, action)
    return text('OK')


async def broadcast(request, action):
    message = {
        'action': action,
        'payload': dict(request.form)
    }
    broadcasts = [send_websocket(request, ws, message) for ws in request.app.ws_clients]
    await asyncio.gather(*broadcasts)

async def send_websocket(request, ws, message):
    try:
        await ws.send(json.dumps(message))
    except ConnectionClosed:
        logging.warning("ConnectionClosed")
        request.app.ws_clients.remove(ws)


async def feed(request, ws):
    request.app.ws_clients.add(ws)
    while True:
        # await ws.send(data)
        data = await ws.recv()
