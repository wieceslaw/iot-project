import asyncio
import datetime
import json
import random
import sys

import websockets
import uuid


async def connect_to_server(address):
    client_id = uuid.uuid4()
    async with websockets.connect(f"ws://{address}:8765/{client_id}") as websocket:
        while True:
            await websocket.send(json.dumps({
                "id": str(uuid.uuid4()),
                "client_id": str(client_id),
                "volume": random.randint(1, 10),
                "created_at": str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            }))
            response = await websocket.recv()
            print(f"Received: {response}")
            await asyncio.sleep(2)


if __name__ == '__main__':
    server_address = sys.argv[1]
    asyncio.get_event_loop().run_until_complete(connect_to_server(server_address))
