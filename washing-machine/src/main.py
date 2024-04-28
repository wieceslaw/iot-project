import asyncio
import json
import uuid

from asyncio_mqtt import Client


async def wash():
    washer_id = str(uuid.uuid4())

    async with Client("localhost") as client:
        await client.publish("washing/register", payload=f"{washer_id}")

        async with client.messages() as messages:
            await client.subscribe(f"washer/{washer_id}")
            async for message in messages:
                order = json.loads(message.payload)
                print(f"Order received: {order}")
                await asyncio.sleep(order["volume"])
                order_done = {
                    "order_id": order["id"],
                    "client_id": order["client_id"],
                }
                await client.publish("washing/done", payload=f"{json.dumps(order_done)}")
                print(f"Order {order['id']} done")


asyncio.run(wash())
