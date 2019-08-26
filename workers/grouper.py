import asyncio
import operator
import itertools
import json
import collections
import logging
from aio_pika import connect_robust, Message, ExchangeType

logging.basicConfig(filename='grouper.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')


async def main(loop):
    connection = await connect_robust(
        "amqp://guest:guest@conejito/",
        loop=loop
    )

    queue_name = 'grouper'
    exchange_name = 'creator'
    routing_key = ''

    # Creating channel
    channel = await connection.channel()

    # Declaring exchange
    exchange = await channel.declare_exchange(
        exchange_name,
        type=ExchangeType.FANOUT,
        auto_delete=False
    )

    # Declaring queue
    queue = await channel.declare_queue(queue_name, auto_delete=False)

    # Binding queue
    await queue.bind(exchange, routing_key)

    logging.warning('Set up')

    out_exchange = await channel.declare_exchange(
        'single',
        type=ExchangeType.DIRECT,
        auto_delete=False
    )
    manager = QueueManager(out_exchange)
    consumer = Consumer(queue, manager.add_message)

    await asyncio.gather(
        consumer.get_messages(),
        manager.consume()
    )


class Consumer:
    def __init__(self, queue, callback):
        self.queue = queue
        self.callback = callback

    async def get_messages(self):
        async with self.queue.iterator() as queue_iter:
            # Cancel consuming after __aexit__
            async for message in queue_iter:
                async with message.process():
                    self.callback(message)


class QueueManager:
    def __init__(self, exchange):
        self.queues = collections.defaultdict(Queue)
        self.exchange = exchange
        Queue.exchange = exchange

    async def consume(self):
        while True:
            tasks = []
            for key, queue in list(self.queues.items()):
                if queue.tick():
                    tasks.append(self.queues.pop(key).consume())

            if tasks:
                await asyncio.gather(*tasks)
            else:
                await asyncio.sleep(1)

    def add_message(self, message):
        try:
            msg = json.loads(message.body)
            key = msg.get('locator', '')
            self.queues[key].add_message(msg)
            logging.warning('Got message %s' % msg)
        except Exception as e:
            logging.error('ERROR WITH MESSAGE %s body=%s, REASON: %s' % (
                message,
                message.body,
                e
            ))


class Queue:
    exchange = None

    def __init__(self):
        self.messages = []
        self.time = 0
        self.routing_key = 'single'

    def tick(self):
        self.time += 1
        return self.time > 5

    async def consume(self):
        grouper_func = operator.itemgetter('locator')
        messages = sorted(self.messages, key=grouper_func)

        for i, (groupper, msgs) in enumerate(itertools.groupby(messages, key=grouper_func)):
            msg = {
                '__count': 0
            }
            for m in msgs:
                msg.update(m)
                msg['__count'] += 1

            body = json.dumps(msg).encode()
            logging.warning('SEND MSG %s' % body)
            await self.exchange.publish(
                Message(
                    body=body
                ),
                routing_key=self.routing_key
            )

    def add_message(self, message):
        self.messages.append(message)


if __name__ == "__main__":
    logging.warning('Start...')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
