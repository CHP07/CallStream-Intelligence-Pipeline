from models import CallPayload
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import aio_pika
import logging


RABBITMQ_URL = "amqp://guest:guest@localhost/"
QUEUE_NAME = "call_center_queue"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("Worker")

@asynccontextmanager
async def lifespan(app:FastAPI):
    connection = None
    try :
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        await channel.declare_queue(QUEUE_NAME, durable=True)

        app.state.rmq_connection = connection
        app.state.rmq_channel = channel

        yield
    except Exception as e:
        raise e
    finally :
        if connection:
            await connection.close()

app = FastAPI(lifespan=lifespan)

@app.post("/api/store")
async def store_data(payload : CallPayload, request : Request):
    try :
        message_body = payload.model_dump_json().encode()
        channel = request.app.state.rmq_channel

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key = QUEUE_NAME
        )

        return {
            "status" : "success",
            "message" : "Data queued for processing...",
            "corellation_id" : payload.Client_Correlation_Id
        }
    except Exception as e:
        return {
            "status" : "error",
            "message" : "Internal Queue Error"
        }