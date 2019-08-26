import asyncio
import json
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
                {
                    'description': 'Partner all notifications',
                    'name': 'WE_WANT_ALL',
                    'url': 'http://creator:5000/notify/booking_created',
                    'payload': {
                        'locator': '$LOCATOR',
                        'partner_name': 'all notifications'
                    }
                },
                {
                    'description': 'Partner booking creations',
                    'name': 'TRIVAGO',
                    'url': 'http://creator:5000/notify/booking_created',
                    'payload': {
                        'locator': '$LOCATOR',
                        'partner_name': 'booking creations'
                    }
                },
            ],
            'booking.modify.#': [
                {
                    'description': 'Partner all notifications',
                    'name': 'WE_WANT_ALL',
                    'url': 'http://creator:5000/notify/booking_modified',
                    'payload': {
                        'locator': '$LOCATOR',
                        'partner_name': 'all notifications'
                    }
                },
                {
                    'description': 'Partner booking modifications',
                    'url': 'http://creator:5000/notify/booking_modified',
                    'name': 'CHECK_MODIFICATIONS',
                    'payload': {
                        'locator': '$LOCATOR',
                        'partner_name': 'all modifications'
                    }
                },
            ],
            'booking.modify.add_room': [
                {
                    'description': 'Partner booking add room',
                    'url': 'http://creator:5000/notify/booking_add_room',
                    'name': 'MOAR_ROOMS',
                    'payload': {
                        'locator': '$LOCATOR',
                        'partner_name': 'room changes'
                    }
                },
            ],
            'booking.cancel': [
                {
                    'description': 'Partner all notifications',
                    'name': 'WE_WANT_ALL',
                    'url': 'http://creator:5000/notify/booking_cancel',
                    'payload': {
                        'locator': '$LOCATOR',
                        'partner_name': 'all modifications'
                    }
                },
                {
                    'description': 'Partner booking cancelations',
                    'name': 'TRIVAGO',
                    'url': 'http://creator:5000/notify/booking_cancel',
                    'payload': {
                        'locator': '$LOCATOR',
                        'partner_name': 'cancelations'
                    }
                },
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

        self.exchange_name = 'creator'
        self.out_exchange_name = 'event_sender'

        # Creating channel
        self.channel = await self.connection.channel()

        # Declaring exchange
        self.exchange = await self.channel.declare_exchange(
            self.exchange_name,
            type=ExchangeType.TOPIC,
            auto_delete=False,
            durable=True
        )

        # Declaring exchange
        self.out_exchange = await self.channel.declare_exchange(
            self.out_exchange_name,
            type=ExchangeType.TOPIC,
            auto_delete=False,
            durable=True
        )

        self.queues = {}
        for topic, partners in self.config.topics.items():
            queue_name = 'event_dispatcher/%s' % topic
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
                    await self.dispatch_message(
                        message,
                        partners,
                        queue_name,
                    )

    async def dispatch_message(self, message, partners, queue_name):
        logging.info('GOT MESSAGE! %s in queue %s with partners %s' % (message.body, queue_name, partners))

        data = json.loads(message.body)

        payload = {
            'original_message': data
        }
        for partner in partners:
            routing_key = 'send_events_to_integrations.%s' % partner['name']
            payload['partner_info'] = partner
            body = json.dumps(payload).encode()
            logging.warning('SEND MSG %s' % payload)
            await self.out_exchange.publish(
                Message(
                    body=body
                ),
                routing_key=routing_key
            )


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
