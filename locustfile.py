import random
import uuid
from datetime import datetime
from locust import HttpUser, task, between

class API1LoadTest(HttpUser):
    # wait_time simulates how long a real user waits between actions.
    # between(1, 3) means each simulated user waits 1 to 3 seconds before hitting the API again.
    # For "Stress Testing" (max load), you can remove this line.
    wait_time = between(1, 3)

    @task
    def send_call_payload(self):
        # 1. Generate Random Data so every request is unique
        correlation_id = str(uuid.uuid4())
        session_id = f"SESS_{random.randint(1000, 9999)}"
        
        # Randomly pick status and type
        status = random.choice(["Answered", "Missed", "Connected"])
        call_type = random.choice(["INBOUND", "OUTBOUND"])
        
        # Current timestamp in the format API-1 expects
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 2. Construct the JSON Payload
        # We match the Pydantic model from API-1 exactly
        payload = {
            "Overall_Call_Status": status,
            "Customer_Name": f"User_{random.randint(1, 1000)}",
            "Client_Correlation_Id": correlation_id,
            "callType": call_type,
            "conversationDuration": round(random.uniform(10.0, 300.0), 2),
            "Overall_Call_Duration": "00:05:00", # Keeping format simple for test
            "Campaign_Id": "CAMP_A",
            "Campaign_Name": "Sales_Team",
            "Caller_ID": "+19876543210",
            "DTMF_Capture": random.choice([0, 1, None]),
            "participants": [
                {
                    "participantAddress": "Agent_007",
                    "participantType": "AGENT",
                    "status": "connected",
                    "duration": 120.5
                }
            ],
            "timestamp": current_time,
            "Session_ID": session_id
        }

        # 3. Send the POST Request
        # self.client acts exactly like 'requests' or 'httpx'
        with self.client.post("/api/receive", json=payload, catch_response=True) as response:
            # 4. Custom Success/Failure Marking
            if response.status_code == 200:
                # We check if the internal logic also said "success"
                json_resp = response.json()
                if json_resp.get("status") == "success":
                    response.success()
                else:
                    response.failure(f"API Logic Error: {json_resp.get('message')}")
            else:
                response.failure(f"HTTP Error: {response.status_code}")