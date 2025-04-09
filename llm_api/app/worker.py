import aio_pika
import json
from .llm_client import LLMClient

async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        client = LLMClient()
        prompt = client.format_prompt(data["context"], data["text"])
        response = client.generate(prompt)
        print(f"Generated response: {response}")

async def main():
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("llm_queue")
        await queue.consume(process_message)
        await asyncio.Future()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())