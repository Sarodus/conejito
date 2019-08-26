import asyncio
import operator
import itertools
import json
import collections
import logging
from aio_pika import connect_robust, Message, ExchangeType


logging.basicConfig(
    # filename='eventdispatcher.log',
    # filemode='w',
    format='%(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class EventDispatcherConfig:
    def __init__(self):
        self.topics = []

    async def set_up(self):
        logging.info('Getting config')
        await asyncio.sleep(.1)
        self.topics = {
            'booking.create': [
                'Partner all notifications',
                'Partner booking creations',
            ],
            'booking.modify.#': [
                'Partner all notifications',
                'Partner booking modifications'
            ],
            'booking.cancel': [
                'Partner all notifications',
                'Partner booking cancelations'
            ]
        }


class EventDispatcher:
    def __init__(self, loop, config):
        self.loop = loop
        self.config = config

    async def set_up(self):
        await self.config.set_up()

        self.connection = await connect_robust(
            "amqp://guest:guest@conejito/",
            loop=loop
        )

        self.queue_name = 'event_dispatcher'
        self.exchange_name = 'creator'

        # Creating channel
        self.channel = await self.connection.channel()

        # Declaring exchange
        self.exchange = await self.channel.declare_exchange(
            self.exchange_name,
            type=ExchangeType.TOPIC,
            auto_delete=False
        )

        self.queues = {}
        for topic, partners in self.config.topics.items():
            queue_name = topic
            queue = await self.channel.declare_queue(
                queue_name,
                auto_delete=False,
                exclusive=True
            )
            self.queues[queue_name] = (queue, partners)

            logging.info('Channel bind to queue %s with partners %s' % (queue_name, partners))
            for partner in partners:
                await queue.bind(
                    exchange=self.exchange_name,
                    routing_key=topic
                )

    async def dispatch(self):
        tasks = [
            self.dispatch_queue(queue_name, queue, partners)
            for queue_name, (queue, partners) in self.queues.items()
        ]
        await asyncio.gather(*tasks)

    async def dispatch_queue(self, queue_name, queue, partners):
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    self.dispatch_message(
                        message,
                        partners,
                        queue_name,
                    )

    def dispatch_message(self, message, partners, queue_name):
        logging.info('GOT MESSAGE! %s in queue %s with partners %s' % (message.body, queue_name, partners))


async def main(loop):
    config = EventDispatcherConfig()
    await config.set_up()

    dispatcher = EventDispatcher(loop, config)
    await dispatcher.set_up()

    tasks = [
        dispatcher.dispatch()
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    logging.warning('Starting EventDispatcher...')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
