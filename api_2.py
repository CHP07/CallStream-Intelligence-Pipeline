import time
import json
from datetime import datetime
from typing import List, Literal, Optional, Union
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import aiomysql
import logging
import sys
from models import CallPayload

# class Participant(BaseModel):
#     participantAddress: str
#     participantType: str
#     status: str
#     duration: float

# class CallPayload(BaseModel):
#     Overall_Call_Status: Literal["Answered", "Missed", "Connected"]
#     Customer_Name: str
#     Client_Correlation_Id: str
#     callType: Literal["OUTBOUND", "INBOUND"]
#     conversationDuration: float
#     Overall_Call_Duration: str
#     Campaign_Id: str
#     Campaign_Name: str
#     Caller_ID: str
#     DTMF_Capture: Optional[Union[Literal[0, 1], None]] = None
#     participants: List[Participant]
#     timestamp: datetime
#     Session_ID: str

class CustomFormatter(logging.Formatter):
    def format(self, record):
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S.%f")[:-3]
        api_name = record.name
        level = record.levelname
        correlation_id = getattr(record, 'correlation_id', 'N/A')
        message = record.getMessage()
        
        return f"[{timestamp}] [{level}] [{api_name}] [{correlation_id}] {message}"

def setup_logger(api_name):
    logger = logging.getLogger(api_name)

    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger

logger = setup_logger("API-2")

DB_CONFIG = {
    'host' : 'localhost',
    'port' : 3306,
    'user' : 'root',
    'password' : '',
    'db' : 'call_center_db',
    'autocommit' : False
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try :
        logger.info("Initializing pool...", extra={"correlation_id" : "SYSTEM"})
        app.state.pool = await aiomysql.create_pool(
            **DB_CONFIG,
            minsize=1,
            maxsize=50,
            pool_recycle=3600
        )
        logger.info("Pool connected to DB....", extra={"correlation_id" : "SYSTEM"})
    except Exception as e:
        logger.error(f"Failed to connect DB : {e}....", exc_info=True, extra={"correlation_id" : "SYSTEM"})
        raise e
    yield
    logger.info("Closing the pool....", extra={"correlation_id" : "SYSTEM"})
    app.state.pool.close()
    await app.state.pool.wait_closed()
    logger.info("Pool closed successfully....", extra={"correlation_id" : "SYSTEM"})

app = FastAPI(lifespan=lifespan)

@app.post("/api/store")
async def store_data(payload : CallPayload, request : Request):

    start_time = time.time()
    participants_json = json.dumps([i.model_dump() for i in payload.participants])

    query = """
        INSERT INTO call_records (
            overall_call_status, customer_name, client_correlation_id, 
            call_type, conversation_duration, overall_call_duration, 
            campaign_id, campaign_name, caller_id, dtmf_capture, 
            participants_data, call_timestamp, session_id, storage_time_ms
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    current_process_time = (time.time() - start_time) * 1000
    values = (
        payload.Overall_Call_Status,
        payload.Customer_Name,
        payload.Client_Correlation_Id,
        payload.callType,
        payload.conversationDuration,
        payload.Overall_Call_Duration,
        payload.Campaign_Id,
        payload.Campaign_Name,
        payload.Caller_ID,
        payload.DTMF_Capture,
        participants_json,
        payload.timestamp,
        payload.Session_ID,
        current_process_time
    )

    record_id = None
    status_msg = "error"
    message = ""

    try :
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, values)
                    await conn.commit()

                    record_id = cur.lastrowid
                    status_msg = "success"
                    message = "Data stored successfully"
                except Exception as e:
                    logger.error(f"DB Inserting Failed : {e}", extra={"correlation_id" : payload.Client_Correlation_Id})
                    await conn.rollback()
                    raise e
    except Exception as e:
        status_msg = "error"
        message = f"Storage failed -> {e}"
        logger.error(f"Critical Error : {e}", extra={"correlation_id" : payload.Client_Correlation_Id})
    
    process_time = (time.time() - start_time) * 1000
    logger.info(f"Insert operation complete. Time: {process_time:.2f}ms", 
                extra={'correlation_id': payload.Client_Correlation_Id})

    return {
        "status" : status_msg,
        "record_id" : record_id,
        "storage_time_ms" : process_time,
        "message" : message
    }


