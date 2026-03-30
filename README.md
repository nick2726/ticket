# 🚀 JARVIS: Multi-Agent Support 

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi) ![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange) ![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-4B32C3) ![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-black)

An end-to-end, multi-agent AI system designed to automate customer support triage, enforce strict company policies via RAG, and act as an intelligent e-commerce assistant. Built for reliability, this system ensures zero-hallucination policy enforcement and knows exactly when to escalate to a human.
This repository contains an end-to-end multi-agent AI system designed to handle customer support tickets. Using LangGraph, the system intelligently triages requests, retrieves relevant store policies, drafts compliance-checked responses, and knows when to escalate to a human agent.

## Features
* **Multi-Agent Orchestration:** Utilizes LangGraph for a robust state machine consisting of Triage, Retriever, Writer, and Compliance agents.
* **RAG-Powered Policy Engine:** Uses ChromaDB and HuggingFace embeddings to ground AI decisions in actual company policy (preventing hallucinations).
* **Strict Compliance Guardrails:** A dedicated compliance agent audits outgoing messages to ensure policies aren't violated and exceptions aren't promised without authorization.
* **REST API & Tool Calling:** Includes an ingestion/chat API built with FastAPI that connects to live store databases and web search.

**Agent Responsibilities & Prompts**
* **Triage Agent:** Acts as the gatekeeper. It analyzes the ticket against the JSON order context. If fields like `item_category` or `order_status` are missing, it conditionally routes the graph to an `END` state and outputs targeted clarifying questions.
* **Retriever Agent:** Activated only if triage passes. It searches a persistent `Chroma` vector database using `HuggingFaceEmbeddings` (`all-MiniLM-L6-v2`) to pull the top 3 most relevant policy chunks based on a combined query of the ticket and order context.
* **Writer Agent:** The core drafter. It is strictly prompted to use the retrieved context to formulate a decision (approve, deny, escalate), provide a rationale, draft the customer-facing message, and explicitly list chunk citations to prove grounding.
* **Compliance Agent:** Acts as an adversarial auditor. It compares the Writer's draft against the raw retrieved policies. If it detects hallucinated promises or user pressure for out-of-policy exceptions, it either triggers an escalation flag or conditionally routes the state *back* to the Writer Agent for a rewrite (capped at 3 loops to prevent infinite recursion).

**Data Sources**
1.  **Policy Vector Store:** A local ChromaDB directory stores embedded chunks of company policies (e.g., return windows, perishable goods exceptions).
2.  **Live Inventory API:** The FastAPI app (`ingest.py`) connects to a local Node.js backend to fetch live pricing and product availability.
3.  **Fallback Web Search:** A DuckDuckGo search tool is utilized if internal documentation lacks technical product specifications.

**Evaluation Summary & Key Failure Modes**
The system was evaluated against three distinct edge cases: standard exceptions (perishables), hostile out-of-policy demands, and missing data scenarios. The multi-agent setup successfully isolated failure modes. 
* *Key Failure Mode 1 (Looping):* Initially, if the Retriever failed to find a policy, the Writer would guess, causing the Compliance agent to reject it and trigger an infinite loop. This was mitigated by introducing a `loop_count` state variable that forces an escalation after 3 failed rewrites.
* *Key Failure Mode 2 (Context Ignorance):* Early testing showed the Retriever missing policies if the ticket didn't explicitly mention keywords. This was fixed by appending the parsed JSON `order_context` directly into the Chroma search query.

**Future Improvements**
In the next iteration, I would implement **Human-in-the-Loop (HITL) interrupt functionality** via LangGraph's native breakpoint features, allowing human supervisors to manually approve rewrites for high-value tickets. Furthermore, I would expand the vector retrieval to use Hybrid Search (BM25 + Dense Embeddings) to improve policy matching for highly specific SKU queries.




## 🧠 Architecture Overview

The core resolution engine is a state-machine orchestrated by **LangGraph**, utilizing **Groq's Llama 3.3 70B** for complex reasoning and **ChromaDB** for semantic policy retrieval.

```mermaid
graph TD
    A[Incoming Ticket + Order JSON] --> B{Triage Agent}
    B -- Missing Context --> C[Halt: Ask Clarifying Qs]
    B -- Context Complete --> D[Retriever Agent]
    D --> E[Writer Agent]
    E --> F{Compliance Auditor}
    F -- Hallucination / Policy Breach --> E
    F -- Out-of-Policy Demand --> G[Escalate to Human]
    F -- 100% Compliant --> H[Final Customer Response]


    ✨ Key Features
Multi-Agent Orchestration: Specialized agents (Triage, Retriever, Writer, Compliance) handle isolated tasks to improve accuracy.

Strict Compliance Guardrails: An adversarial compliance agent audits all outgoing drafts. If a draft promises unauthorized exceptions, it is rejected and re-routed for a rewrite.

Live Store Integration: The FastAPI ingest.py service connects to a live Node.js backend to fetch real-time product inventory and pricing.

Web Search Fallback: Uses DuckDuckGoSearchRun to find technical specifications for items not strictly detailed in the store database.

🛠️ Setup & Installation
1. Clone the repository

Bash
git clone <your-repo-link>
cd ticket-main
2. Install dependencies

Bash
pip install -r requirements.txt
3. Environment Variables
Create a .env file in the root directory:

Code snippet
GROQ_API_KEY=your_api_key_here
🚀 Running the System
Run the LangGraph Support Agent Evaluation:
Tests the multi-agent graph against 3 core scenarios: standard exceptions, hostile escalations, and missing data.

Bash
python agent.py
Run the JARVIS E-Commerce Assistant API:
Spins up the FastAPI server on http://127.0.0.1:5000.

Bash
uvicorn ingest:app --host 127.0.0.1 --port 5000

---

### 2. The Refined 1-Page Write-Up
*Save this as a PDF or Markdown file (e.g., `Architecture_WriteUp.md`) to include with your submission.*

```markdown
# Engineering Write-Up: Multi-Agent Resolution System

### Architecture & Philosophy
The system is built on a state-machine architecture using **LangGraph**, deliberately moving away from naive zero-shot prompting to a deterministic, node-based workflow. By dividing the resolution process into isolated, specialized agents (Triage, Retrieval, Writing, Compliance), the system significantly reduces hallucinations and ensures strict adherence to company guidelines. 

The application utilizes **Groq** to power the Llama 3 models, specifically leveraging `llama-3.3-70b-versatile` for deep reasoning in the support graph and `llama-3.1-8b-instant` for low-latency tool calling in the live ingest API.

### Agent Responsibilities
1. **Triage Agent (Gatekeeper):** Parses the order JSON. If critical fields (`item_category`, `order_status`) are missing, it halts the graph entirely (routing to `END`) to ask clarifying questions, preventing the system from guessing.
2. **Retriever Agent (RAG Engine):** Uses `HuggingFaceEmbeddings` (`all-MiniLM-L6-v2`) and ChromaDB to fetch the top 3 relevant policy chunks based on the combined ticket and order context.
3. **Writer Agent (Drafter):** Formulates the customer response and decision rationale. It is strictly prompted to include exact citation chunks (e.g., `[Doc: X | Chunk: Y]`).
4. **Compliance Agent (Auditor):** An adversarial node that reviews the draft against the retrieved context. It catches out-of-policy promises or unauthorized escalations. If it fails the draft, it loops back to the Writer for a rewrite (capped at 3 loops to prevent infinite recursion).

### Evaluation Summary & Edge Cases Handled
The system was evaluated against three distinct failure modes:
* **Perishable Exception:** Correctly identifies a melted item, successfully denies the standard return based on the retrieved perishable policy, and cites the specific rule.
* **Hostile Out-of-Policy Demand:** Rejects a 30+ day return demand from an "influencer." The Compliance agent catches the pressure and flags `escalate: True`.
* **Missing Data Abstention:** Successfully halts execution when the order status is missing, returning a clarifying question instead of hallucinating an answer.

### Next Steps & Improvements
1. **Hybrid Retrieval:** Upgrade the ChromaDB dense retriever to a Hybrid Search (Dense + BM25) to better handle exact SKU matches or specific policy ID numbers.
2. **Human-in-the-Loop (HITL):** Implement LangGraph's native breakpoint features
