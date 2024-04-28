import asyncio
import json
import random

import websockets
from asyncio_mqtt import Client
from websockets import ConnectionClosedError

clients = {}
washers = []


async def on_connect(websocket, path):
    client_id = path.lstrip("/")
    print(f"Client connected, id:{client_id}")
    clients[client_id] = websocket
    try:
        async with Client("localhost") as client:
            async for message in websocket:
                print(f"Client[{client_id}]: {message}")
                random_washer_id = random.choice(washers)
                await client.publish(f"washer/{random_washer_id}", message)
    except ConnectionClosedError:
        pass
    clients.pop(client_id)
    print(f"Client disconnected, id:{client_id}")


async def on_washer_connect():
    async with Client("localhost") as client:
        async with client.messages() as messages:
            await client.subscribe("washing/register")
            async for message in messages:
                washer_id = message.payload.decode("utf-8")
                print(f"Washer id={washer_id} connected")
                washers.append(washer_id)


async def on_washer_done():
    async with Client("localhost") as client:
        async with client.messages() as messages:
            await client.subscribe("washing/done")
            async for message in messages:
                order_done = json.loads(message.payload.decode("utf-8"))
                order_client_id = order_done["client_id"]
                print(f"Order done for client: {order_client_id}")
                if order_client_id in clients:
                    print("Sending results to client...")
                    websocket = clients[order_client_id]
                    await websocket.send(f"Finished order {order_done}")


async def main():
    await asyncio.gather(
        on_washer_done(),
        on_washer_connect(),
        websockets.serve(on_connect, "localhost", 8765),
    )


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
