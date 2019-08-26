import asyncio
import operator
import itertools
import json
import queue
import logging
from aio_pika import connect_robust, Message, ExchangeType

logging.basicConfig(filename='grouper.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')


messages_queue = queue.Queue()


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

    await asyncio.gather(
        get_messages(channel, exchange, queue),
        group_messages(channel)
    )


async def get_messages(channel, exchange, queue):
    async with queue.iterator() as queue_iter:
        # Cancel consuming after __aexit__
        async for message in queue_iter:
            async with message.process():
                msg = json.loads(message.body)
                logging.warning('Got message %s' % msg)
                messages_queue.put(msg)


async def group_messages(channel):
    exchange_name = 'single'
    routing_key = 'single'
    exchange = await channel.declare_exchange(
        exchange_name,
        type=ExchangeType.DIRECT,
        auto_delete=False
    )

    while True:
        await asyncio.sleep(10)
        messages = []
        while not messages_queue.empty():
            messages.append(messages_queue.get())


        grouper_func = operator.itemgetter('locator')
        messages = sorted(messages, key=grouper_func)

        for i, (groupper, msgs) in enumerate(itertools.groupby(messages, key=grouper_func)):
            body = json.dumps(next(msgs)).encode()
            await exchange.publish(
                Message(
                    body=body
                ),
                routing_key=routing_key
            )

        logging.warning('Group %s messages into %s' % (
            len(messages),
            i
        ))


if __name__ == "__main__":
    logging.warning('Start...')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
