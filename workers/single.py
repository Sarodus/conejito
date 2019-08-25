import asyncio
import json
import logging
from aio_pika import connect_robust, Message, ExchangeType

logging.basicConfig(filename='single.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')


async def main(loop):
    connection = await connect_robust(
        "amqp://guest:guest@conejito/",
        loop=loop
    )

    queue_name = 'single'
    exchange_name = 'single'
    routing_key = 'single'

    # Creating channel
    channel = await connection.channel()

    # Declaring exchange
    exchange = await channel.declare_exchange(
        exchange_name,
        type=ExchangeType.DIRECT,
        auto_delete=False
    )

    # Declaring queue
    queue = await channel.declare_queue(queue_name, auto_delete=False)

    # Binding queue
    await queue.bind(exchange, routing_key)

    async with queue.iterator() as queue_iter:
        # Cancel consuming after __aexit__
        async for message in queue_iter:
            async with message.process():
                msg = json.loads(message.body)
                logging.warning('Got message %s' % msg)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
