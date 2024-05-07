import asyncio
import sys
from datetime import datetime
import json
import uuid

from asyncio_mqtt import Client


async def wash(address):
    washer_id = str(uuid.uuid4())

    async with Client(address) as client:
        await client.publish("washing/register", payload=f"{washer_id}")

        async with client.messages() as messages:
            await client.subscribe(f"washer/{washer_id}")
            async for message in messages:
                order = json.loads(message.payload)
                print(f"Order received: {order}")
                await asyncio.sleep(order["volume"])
                created_at = datetime.strptime(order["created_at"], '%Y-%m-%d %H:%M:%S')
                finished_at = datetime.now()
                order_done = {
                    "order_id": order["id"],
                    "client_id": order["client_id"],
                    "created_at": order["created_at"],
                    "finished_at": str(finished_at.strftime('%Y-%m-%d %H:%M:%S')),
                    "volume": order["volume"],
                    "took_seconds": str((finished_at - created_at).seconds),
                }
                await client.publish("washing/done", payload=f"{json.dumps(order_done)}")
                print(f"Order {order['id']} done")

        await client.publish("washing/deregister", payload=f"{washer_id}")


if __name__ == '__main__':
    server_address = sys.argv[1]
    asyncio.run(wash(server_address))
