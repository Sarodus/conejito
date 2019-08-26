import asyncio
import operator
import itertools
import json
import collections
import requests_async as requests
import logging
from aio_pika import connect_robust, Message, ExchangeType


logging.basicConfig(
    # filename='eventsender.log',
    # filemode='w',
    format='%(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class EventSender:
    def __init__(self, loop):
        self.loop = loop

    async def set_up(self):
        self.connection = await connect_robust(
            "amqp://guest:guest@conejito/",
            loop=loop
        )

        self.queue_name = 'send_event'
        self.exchange_name = 'event_sender'

        # Creating channel
        self.channel = await self.connection.channel()

        # Declaring exchange
        self.exchange = await self.channel.declare_exchange(
            self.exchange_name,
            type=ExchangeType.TOPIC,
            auto_delete=False,
            durable=True
        )

        self.queue = await self.channel.declare_queue(
            self.queue_name,
            auto_delete=False,
            durable=True
        )

        await self.queue.bind(
            exchange=self.exchange_name,
            routing_key='send_events_to_integrations.#'
        )

    async def dispatch(self):
        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await self.dispatch_message(
                        message
                    )

    async def dispatch_message(self, message):
        logging.info('GOT MESSAGE! %s' % (message.body))


        data = json.loads(message.body)
        original_data = data['original_message']
        partner_info = data['partner_info']
        payload = partner_info.get('payload')

        if payload:
            for key, val in payload.items():
                if val == '$LOCATOR':
                    payload[key] = original_data['locator']

        url = partner_info['url']
        logging.info('REQUEST TO %s WITH %s' % (url, payload))
        response = await requests.post(
            url,
            data=payload
        )
        logging.info('RESPONSE: %s' % response.text)


async def main(loop):
    emiter = EventSender(loop)
    await emiter.set_up()

    tasks = [
        emiter.dispatch()
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    logging.warning('Starting EventSender...')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
