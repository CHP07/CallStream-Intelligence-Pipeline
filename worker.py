import json
import aio_pika
import time
import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import asyncio
import logging

RABBITMQ_URL = "amqp://guest:guest@localhost/"
QUEUE_NAME = "call_center_queue"
DB_CONFIG = {
    "user" : "root",
    "host" : "localhost",
    "port" : 3306,
    "db" : "call_center_db",
    "password" : "",
    "autocommit" : True
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("Worker")

BATCH_SIZE = 500
FLUSH_INTERVAL = 2

buffer = []
last_flush_time = time.time()

async def get_db():
    return await aiomysql.create_pool(**DB_CONFIG, maxsize=5, minsize=1)

async def flush_buffer(pool):
    global buffer, last_flush_time

    if not buffer:
        return

    records_to_insert = buffer[:]
    buffer.clear()
    last_flush_time = time.time()

    query = """ 
            INSERT INTO call_records (
                overall_call_status, customer_name, client_correlation_id, 
                call_type, conversation_duration, overall_call_duration, 
                campaign_id, campaign_name, caller_id, dtmf_capture, 
                participants_data, call_timestamp, session_id, storage_time_ms
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
        """
    
    try :
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(query, records_to_insert)
        logger.info(f"✅ Batch inserted {len(records_to_insert)} records.")
    except Exception as e:
        print("***********************")
        print(e)
        print("***********************")
        logger.error(f"❌ DB Insert Failed: {e}")


async def process_message(message : aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        payload = json.loads(message.body.decode())

    record = (
            payload['Overall_Call_Status'],
            payload['Customer_Name'],
            payload['Client_Correlation_Id'],
            payload['callType'],
            payload['conversationDuration'],
            payload['Overall_Call_Duration'],
            payload['Campaign_Id'],
            payload['Campaign_Name'],
            payload['Caller_ID'],
            payload['DTMF_Capture'],
            json.dumps(payload['participants']), # Serialize list to JSON string
            payload['timestamp'],
            payload['Session_ID']
        )
    
    buffer.append(record)



async def main():
    pool = await get_db()
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    await channel.set_qos(prefetch_count=500)

    queue = await channel.declare_queue(QUEUE_NAME, durable=True)

    logger.info("Worker Started ✅. Waiting for messages...")
    async def consume_loop():
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await process_message(message)

                # logger.info("From CONSUME LOOP 👋🏻...")
                if len(buffer) >= BATCH_SIZE:
                    await flush_buffer(pool)

    async def time_loop():
        while True:
            await asyncio.sleep(1)
            # logger.info("From TIME LOOP 🕦...")
            if buffer and (time.time() - last_flush_time >= FLUSH_INTERVAL):
                await flush_buffer(pool)
    
    await asyncio.gather(consume_loop(), time_loop())

if __name__ == "__main__":
    try :
        asyncio.run(main())
    except Exception as e:
        print(e)