import time
import httpx
from datetime import datetime
from typing import List, Literal, Optional, Union
from fastapi import FastAPI, Request, status, Response, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import logging
import sys

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

logger = setup_logger("API-1")

@asynccontextmanager
async def lifespan(app:FastAPI):
    try:
        logger.info("Setting up httpx-Client...", extra={"correlation_id" : "SYSTEM"})
        app.state.client = httpx.AsyncClient()
    except Exception as e:
        raise e
    yield
    logger.info("Closing httpx-Client...", extra={"correlation_id" : "SYSTEM"})
    await app.state.client.aclose()
    logger.info("Closed httpx-Client...", extra={"correlation_id" : "SYSTEM"})


class Participant(BaseModel):
    participantAddress: str
    participantType: str
    status: str
    duration: float

class CallPayload(BaseModel):
    Overall_Call_Status: Literal["Answered", "Missed", "Connected"]
    Customer_Name: str
    Client_Correlation_Id: str
    callType: Literal["OUTBOUND", "INBOUND"]
    conversationDuration: float
    Overall_Call_Duration: str = Field(..., pattern=r"^\d{2}:\d{2}:\d{2}$")
    Campaign_Id: str
    Campaign_Name: str
    Caller_ID: str
    DTMF_Capture: Optional[Union[Literal[0, 1], None]] = None
    participants: List[Participant]
    timestamp: datetime  # Auto-parses "YYYY-MM-DD HH:MM:SS"
    Session_ID: str



app = FastAPI(lifespan = lifespan)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request : Request, err : RequestValidationError):
    correlation_id = "unknown"
    logger.info("Validation error...", extra={"correlation_id" : "SYSTEM"})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status" : "error",
            "message" : f"Validation failed : {err.errors()[0]['msg']}",
            "correlation_id" : correlation_id,
            "processing_time_ms" : 0
        }
    )


@app.post("/api/receive")
async def receive_data(payload : CallPayload, request : Request):
    start_time = time.time()
    correlation_id = payload.Client_Correlation_Id
    api_2_url = "http://127.0.0.1:8001/api/store"
    try : 
        response = await request.app.state.client.post(
            api_2_url,
            json = payload.model_dump(mode="json"),
            timeout = 10.0
        )
        response.raise_for_status()
        if "application/json" in response.headers.get("content-type", ""):
            data = response.json()
        else:
            # Fallback for HTML error pages or empty responses
            data = {"error": "Invalid response format", "raw_body": response.text[:100]}
        success = response.status_code < 400
        success_status = "success" if success else "error"
        message = "Data successfully sent!" if success else f"API_2 returned {response.status_code}"
        time_taken = (time.time() - start_time)*1000

    except Exception as e:
        logger.error("Data forwarding failed...", extra={"correlation_id" : payload.Client_Correlation_Id})
        success_status = "error"
        message = f"Data forwarding failed => {type(e).__name__}"
        time_taken = 0

    return {
        "status": success_status,
        "message": message,
        "correlation_id": correlation_id,
        "processing_time_ms": time_taken,
        "api-2-response" : data
    }


# @app.post("/api/store", status_code=status.HTTP_200_OK)
# async def store_data(payload: CallPayload):
#     """
#     Receives CallPayload data and returns a 200 OK status with an empty body.
#     """
#     # Logic to process or save 'payload' would go here
#     return Response(status_code=status.HTTP_200_OK)






















