import logging
import time
from typing import Optional
import sys
from fastapi import FastAPI, Request
from pydantic import BaseModel 
from contextlib import asynccontextmanager
import aiomysql


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

logger = setup_logger("API-3")





DB_CONFIG = {
    "port" : 3306,
    "host" : "localhost",
    "user" : "root",
    "password" : "",
    "autocommit" : False,
    "db" : "call_center_db"
}

@asynccontextmanager
async def lifespan(app:FastAPI):
    logger.info("Setting up API-3...", extra = {"correlation_id" : "SYSTEM"})
    try:
        app.state.pool = await aiomysql.create_pool(
            **DB_CONFIG,
            minsize = 1,
            maxsize = 50,
        )
        logger.info("DB connected successfully...", extra = {"correlation_id" : "SYSTEM"})
    except Exception as e:
        logger.error("DB connection failed....", extra={"correlation_id" : "SYSTEM"})
        raise e
    yield
    logger.info("Closing DB_Pool...", extra={"correlation_id":"SYSTEM"})
    app.state.pool.close()
    await app.state.pool.wait_closed()
    logger.info("Logger closed successfully", extra={"correlation_id" : "SYSTEM"})



def build_where_clause(
    campaign_name: Optional[str], dtmf: Optional[str], 
    call_status: Optional[str], call_type: Optional[str],
    date_from: Optional[str], date_to: Optional[str]
):
    conditions = []
    params = []

    if campaign_name:
        conditions.append("campaign_name = %s")
        params.append(campaign_name)

    if dtmf is not None:
        if dtmf.lower() == 'null':
            conditions.append("dtmf_capture IS NULL")
        else:
            conditions.append("dtmf_capture = %s")
            params.append(int(dtmf))
    
    if call_status:
        conditions.append("overall_call_status = %s")
        params.append(call_status)
    
    if call_type:
        conditions.append("call_type = %s")
        params.append(call_type)

    if date_from:
        conditions.append("call_timestamp >= %s")
        params.append(date_from)

    if date_to:
        conditions.append("call_timestamp <= %s")
        params.append(date_to)

    where_sql = " WHERE " + " AND ".join(conditions) if conditions else ""
    return where_sql, params    


app = FastAPI(lifespan=lifespan)

@app.get("/api/monitor/summary")
async def get_summary(
    request : Request,
    campaign_name: Optional[str] = None,
    dtmf: Optional[str] = None,
    call_status: Optional[str] = None,
    call_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    correlation_id = "MONITOR-" + str(int(time.time()))
    logger.info(f"Query received. Filters: Campaign={campaign_name}, Status={call_status}", 
                extra={'correlation_id': correlation_id})
    
    start_time = time.time()
    where_sql, params = build_where_clause(campaign_name, dtmf, call_status, call_type, date_from, date_to)

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(f"SELECT COUNT(*) as total FROM call_records {where_sql}", params)
            total_calls = (await cur.fetchone())['total']
            camp_query = f"""
                SELECT campaign_name, COUNT(*) as total,
                SUM(CASE WHEN overall_call_status='Answered' THEN 1 ELSE 0 END) as answered,
                SUM(CASE WHEN overall_call_status='Missed' THEN 1 ELSE 0 END) as missed,
                SUM(CASE WHEN overall_call_status='Connected' THEN 1 ELSE 0 END) as connected
                FROM call_records {where_sql} GROUP BY campaign_name
            """
            await cur.execute(camp_query, params)
            by_campaign = await cur.fetchall()
            dtmf_query = f"""
                SELECT dtmf_capture as dtmf_value, COUNT(*) as total,
                SUM(CASE WHEN overall_call_status='Answered' THEN 1 ELSE 0 END) as answered,
                SUM(CASE WHEN overall_call_status='Missed' THEN 1 ELSE 0 END) as missed,
                SUM(CASE WHEN overall_call_status='Connected' THEN 1 ELSE 0 END) as connected
                FROM call_records {where_sql} GROUP BY dtmf_capture
            """
            await cur.execute(dtmf_query, params)
            by_dtmf = await cur.fetchall()
            # 4. Breakdown by Call Status (with percentage)
            status_query = f"SELECT overall_call_status as status, COUNT(*) as count FROM call_records {where_sql} GROUP BY overall_call_status"
            await cur.execute(status_query, params)
            by_status = await cur.fetchall()
            for item in by_status:
                item['percentage'] = round((item['count'] / total_calls * 100), 2) if total_calls > 0 else 0
            # 5. Breakdown by Call Type
            try :
                logger.info("Executing 'call_type' block...", extra={'correlation_id': correlation_id})
                type_query = f"SELECT call_type as type, COUNT(*) as count FROM call_records {where_sql} GROUP BY call_type"
                await cur.execute(type_query, params)
                by_call_type = await cur.fetchall()
            except Exception as e:
                logger.error("Code crashed in 'call_type' block...", extra={'correlation_id': correlation_id})
                logger.error(f"Failed sql query... : {type_query}", extra={'correlation_id': correlation_id})
                logger.error(f"params : {params}", extra={'correlation_id': correlation_id})
                by_status = []
            # 6. Performance Metrics (Avg times)
            perf_query = f"""
                SELECT AVG(processing_time_ms) as avg_processing, 
                    AVG(storage_time_ms) as avg_storage 
                FROM call_records {where_sql}
            """
            await cur.execute(perf_query, params)
            perf_data = await cur.fetchone()
        
    logger.info("Response generation complete.", extra={'correlation_id': correlation_id})

    return {
        "summary": {
            "total_calls": total_calls,
            "by_campaign": by_campaign,
            "by_dtmf": by_dtmf,
            "by_call_status": by_status,
            "by_call_type": by_call_type,
            "performance_metrics": {
                "avg_processing_time_ms": round(perf_data['avg_processing'] or 0, 2),
                "avg_storage_time_ms": round(perf_data['avg_storage'] or 0, 2),
                "total_requests": total_calls,
                "successful_requests": total_calls 
            }
        },
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }




