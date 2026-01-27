# 🤖 Call Center Data Analyst (ReAct Agent)

This component is an Intelligent AI Agent built with **LangGraph** and **Google Gemini 2.0 Flash**. It is designed to act as a natural language interface for the Call Center Analytics Pipeline, specifically interacting with **API-3 (Monitoring API)** to retrieve and synthesize data insights.

## 🌟 Key Features

-   **Natural Language Querying:** Ask questions like "How many calls did we miss in the Sales campaign last week?" instead of writing SQL or manual API calls.
-   **ReAct Architecture:** Uses a **Reasoning and Acting (ReAct)** loop. The agent analyzes the user's prompt, decides which tool to call, executes the tool, and then summarizes the result for the user.
-   **Parameter Mapping:** The agent is intelligent enough to map natural language entities (like campaign names or dates) into specific API query parameters:
    -   `campaign_name`
    -   `call_status` (Answered, Missed, Connected)
    -   `call_type` (INBOUND, OUTBOUND)
    -   `date_from` / `date_to` (Timestamps)
-   **Persistence:** Built-in `SqliteSaver` allows the agent to remember the context of the conversation across multiple turns.

## 🛠️ Tech Stack

-   **LLM:** Google Gemini 2.0 Flash (`gemini-2.5-flash`)
-   **Framework:** LangGraph (StateGraph architecture)
-   **Agent Pattern:** ReAct (Reason-Action)
-   **Networking:** `httpx` for asynchronous API communication
-   **Persistence:** `langgraph-checkpoint-sqlite`

## 🧩 Agent Logic Flow

1.  **Input:** User provides a query in natural language.
2.  **Reasoning:** The LLM decides if it needs to call the `call_center_info` tool based on the `PROMPT` guidelines.
3.  **Action:** If a tool is needed, the agent constructs a specific URL with query parameters and performs a `GET` request to API-3.
4.  **Observation:** The agent receives the JSON response from the API.
5.  **Output:** The agent synthesizes the raw JSON data into a human-readable summary, highlighting performance metrics and call breakdowns.

## 🚀 How to Run in Colab

1.  **Install Dependencies:**
    ```python
    pip install langchain-google-genai langgraph-checkpoint-sqlite
    ```
2.  **Set Up API Keys:**
    Add your `GEMINI_API_KEY` to the Colab Secrets (the key icon on the left sidebar).
3.  **Configure API Endpoint:**
    Ensure the `Base URL` in the `PROMPT` variable matches your live API-3 tunnel address (e.g., `https://your-tunnel-url.ms/api/monitor/summary`).
4.  **Interact:**
    Use the `graph.stream()` loop to start a conversation with the analyst.

## 📊 Example Interaction

> **User:** "Tell me about the calls before 2024."
> 
> **Agent Thought:** I need to check the total calls with a `date_to` filter set to 2024-01-01.
> 
> **Tool Call:** `GET /api/monitor/summary?date_to=2024-01-01 00:00:00`
> 
> **Final Response:** "There was 1 call before 2024. It was an Inbound call for the 'Sales_Q1' campaign and was successfully Answered."

---
*Note: This agent requires API-3 to be reachable via a public tunnel (like Dev Tunnels or Ngrok) if running from Google Colab.*
