from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from datetime import datetime
from typing import Optional, Literal, Union, List
from pydantic import BaseModel

class Base(DeclarativeBase):
    pass

class CallRecord(Base):
    __tablename__ = "call_records"

    # We define the columns to match your existing DB exactly
    id: Mapped[int] = mapped_column(primary_key=True)
    overall_call_status: Mapped[Optional[str]]
    customer_name: Mapped[Optional[str]]
    client_correlation_id: Mapped[str]
    call_type: Mapped[Optional[str]]
    conversation_duration: Mapped[Optional[float]]
    overall_call_duration: Mapped[Optional[str]]
    campaign_id: Mapped[Optional[str]]
    campaign_name: Mapped[Optional[str]]
    caller_id: Mapped[Optional[str]]
    dtmf_capture: Mapped[Optional[int]]
    
    # Using JSON type for participants allows us to query inside it if needed later
    participants_data: Mapped[Optional[dict]] = mapped_column(JSON)
    
    call_timestamp: Mapped[Optional[datetime]]
    session_id: Mapped[Optional[str]]
    
    # Performance metrics we added earlier
    processing_time_ms: Mapped[Optional[float]]
    storage_time_ms: Mapped[Optional[float]]




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
    Overall_Call_Duration: str
    Campaign_Id: str
    Campaign_Name: str
    Caller_ID: str
    DTMF_Capture: Optional[Union[Literal[0, 1], None]] = None
    participants: List[Participant]
    timestamp: datetime
    Session_ID: str