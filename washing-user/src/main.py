import asyncio
import json
import random

import websockets
import uuid


async def connect_to_server():
    client_id = uuid.uuid4()
    async with websockets.connect(f"ws://localhost:8765/{client_id}") as websocket:
        while True:
            await websocket.send(json.dumps({
                "id": str(uuid.uuid4()),
                "client_id": str(client_id),
                "volume": random.randint(1, 10)
            }))
            response = await websocket.recv()
            print(f"Received: {response}")
            await asyncio.sleep(2)


asyncio.get_event_loop().run_until_complete(connect_to_server())
