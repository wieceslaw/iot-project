import asyncio
import datetime
import json
import random
import sys

import websockets
from asyncio_mqtt import Client
from prometheus_client import start_http_server, Summary, Gauge
from websockets import ConnectionClosedError

clients = {}
washers = []

SERVER_CLIENTS_GAUGE = Gauge('server_clients', 'Description of my counter')
WASHING_MACHINES_GAUGE = Gauge('washing_machines', 'Description of my counter')
REQUEST_TIME_SUMMARY = Summary('washing_server_requests', 'Time spent in request')
WASHING_TIME_SUMMARY = Summary('washing_time', 'Time spent in washing')


async def on_connect(websocket, path, address):
    SERVER_CLIENTS_GAUGE.inc()
    client_id = path.lstrip("/")
    print(f"Client connected, id:{client_id}")
    clients[client_id] = websocket
    try:
        async with Client(address) as client:
            async for message in websocket:
                print(f"Client[{client_id}]: {message}")
                start = datetime.datetime.now()
                random_washer_id = random.choice(washers)
                await client.publish(f"washer/{random_washer_id}", message)
                end = datetime.datetime.now()
                REQUEST_TIME_SUMMARY.observe((end - start).microseconds)
    except ConnectionClosedError:
        pass
    clients.pop(client_id)
    SERVER_CLIENTS_GAUGE.dec()
    print(f"Client disconnected, id:{client_id}")


async def on_washer_connect(address):
    async with Client(address) as client:
        async with client.messages() as messages:
            await client.subscribe("washing/register")
            async for message in messages:
                WASHING_MACHINES_GAUGE.inc()
                washer_id = message.payload.decode("utf-8")
                print(f"Washer id={washer_id} connected")
                washers.append(washer_id)


async def on_washer_disconnect(address):
    async with Client(address) as client:
        async with client.messages() as messages:
            await client.subscribe("washing/deregister")
            async for message in messages:
                WASHING_MACHINES_GAUGE.dec()
                washer_id = message.payload.decode("utf-8")
                print(f"Washer id={washer_id} disconnected")
                washers.remove(washer_id)


async def on_washer_done(address):
    async with Client(address) as client:
        async with client.messages() as messages:
            await client.subscribe("washing/done")
            async for message in messages:
                order = json.loads(message.payload.decode("utf-8"))
                order_client_id = order["client_id"]
                WASHING_TIME_SUMMARY.observe(int(order["took_seconds"]))
                print(f"Order done for client: {order_client_id}")
                if order_client_id in clients:
                    print("Sending results to client...")
                    websocket = clients[order_client_id]
                    await websocket.send(f"Finished order {order}")


async def main(address):
    await asyncio.gather(
        on_washer_done(address),
        on_washer_connect(address),
        on_washer_disconnect(address),
        websockets.serve(lambda websocket, path: on_connect(websocket, path, address), "0.0.0.0", 8765),
    )


if __name__ == '__main__':
    start_http_server(8000)

    server_address = sys.argv[1]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main(server_address))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
