import os
import requests
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent 
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool # <-- NEW IMPORT

# 1. Load Environment Variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    print("🔴 ERROR: GROQ_API_KEY is missing from .env file!")

app = FastAPI()

# 2. Initialize the Groq LLM
llm = ChatGroq(
    groq_api_key=groq_api_key, 
    model_name="llama-3.1-8b-instant",
    temperature=0.3 # Lowered slightly so it stays focused on factual inventory
)

# 3. --- CREATE THE CUSTOM DATABASE TOOL ---
@tool
def search_store_inventory(query: str) -> str:
    """
    Use this tool FIRST to search the store's actual database for products, prices, and availability.
    Input should be a simple search term like 'camera', 'perfume', or 'watch'.
    """
    try:
        # ⚠️ IMPORTANT: Change '8080' to whatever port your Node.js backend is running on!
        node_backend_url = f"http://127.0.0.1:8080/api/search?q={query}"
        
        response = requests.get(node_backend_url)
        if response.status_code == 200:
            data = response.json()
            
            # If the Node server found products, format them for the AI to read
            if data.get("data") and len(data["data"]) > 0:
                results = []
                for item in data["data"]:
                    name = item.get("productName", "Unknown")
                    price = item.get("sellingPrice", "N/A")
                    category = item.get("category", "N/A")
                    results.append(f"- {name} (Category: {category}) : ₹{price}")
                
                return "Found these products in our store's live database:\n" + "\n".join(results)
            else:
                return "No products found in the store matching that query."
        else:
            return "Error connecting to the store database."
    except Exception as e:
        return f"Database search failed: {str(e)}"

# 4. Give JARVIS both tools (Database Search + Web Search)
web_search_tool = DuckDuckGoSearchRun()
tools = [search_store_inventory, web_search_tool]

# 5. Update the System Prompt to prioritize your store
system_message = """You are JARVIS, an intelligent AI shopping assistant for Nikhil's E-Commerce Store.

CRITICAL INSTRUCTIONS:
1. ALWAYS use the `search_store_inventory` tool FIRST to check if we sell the product the user is asking about.
2. If the product IS in our store, give them the details and price based on the tool's output. Encourage them to buy it.
3. If the user asks for technical specs that aren't in the database, OR if we don't carry the item, use the `duckduckgo_search` tool to find that information online. 
4. If we don't have it, tell them it's currently out of stock, but summarize the web search information for them anyway. Keep answers concise.
"""

# 6. Initialize the LangChain Agent
agent_executor = create_agent(model=llm, tools=tools, prompt=system_message)

# 7. The API Endpoint
@app.get("/ai-chat")
async def ai_chat(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        response = agent_executor.invoke({"messages": [HumanMessage(content=query)]})
        final_answer = response["messages"][-1].content
        
        return {
            "success": True,
            "answer": final_answer
        }
    except Exception as e:
        print(f"🔴 AI Error: {e}")
        return {
            "success": False,
            "answer": "I'm having a little trouble connecting to my database right now. Please try again in a moment!"
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting JARVIS (Database Connected) on http://127.0.0.1:5000")
    uvicorn.run(app, host="127.0.0.1", port=5000)
