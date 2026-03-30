# 🚀 JARVIS: Multi-Agent Support & E-Commerce Resolution System

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi) ![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange) ![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-4B32C3) ![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-black)

An end-to-end, multi-agent AI system designed to handle customer support tickets and act as an intelligent e-commerce assistant. Using LangGraph, the system intelligently triages requests, retrieves relevant store policies via RAG, drafts compliance-checked responses, and ensures zero-hallucination policy enforcement—escalating to a human agent only when exactly necessary.

## ✨ Key Features
* **Multi-Agent Orchestration:** Utilizes LangGraph for a robust state machine consisting of specialized Triage, Retriever, Writer, and Compliance agents handling isolated tasks to improve accuracy.
* **RAG-Powered Policy Engine:** Uses ChromaDB and HuggingFace embeddings to ground AI decisions in actual company policy, preventing hallucinations.
* **Strict Compliance Guardrails:** An adversarial compliance agent audits all outgoing drafts. If a draft promises unauthorized exceptions, it is rejected and re-routed for a rewrite.
* **Live Store Integration:** Includes an ingestion/chat API built with FastAPI that connects to live Node.js backends to fetch real-time product inventory and pricing.
* **Web Search Fallback:** Utilizes DuckDuckGoSearchRun to find technical specifications for items not strictly detailed in the store database.

## 🧠 Architecture Overview

The core resolution engine is a state-machine orchestrated by **LangGraph**, utilizing **Groq's Llama 3.3 70B** for complex reasoning and **ChromaDB** for semantic policy retrieval.

```mermaid
graph TD
    A[Incoming Ticket + Order JSON] --> B{Triage Agent}
    B -- Missing Context --> C[Halt: Ask Clarifying Qs]
    B -- Context Complete --> D[Retriever Agent]
    D --> E[Writer Agent]
    E --> F{Compliance Auditor}

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

***

### 2. The Engineering Write-Up
*Save this as a PDF or Markdown file (e.g., `Architecture_WriteUp.md`) to include with your submission.*

```markdown
# Engineering Write-Up: Multi-Agent Resolution System

### Architecture & Philosophy
The system is built on a state-machine architecture using **LangGraph**, deliberately moving away from naive zero-shot prompting to a deterministic, node-based workflow. By dividing the resolution process into isolated, specialized agents (Triage, Retrieval, Writing, Compliance), the system significantly reduces hallucinations and ensures strict adherence to company guidelines. 

The application utilizes **Groq** to power the Llama 3 models, specifically leveraging `llama-3.3-70b-versatile` for deep reasoning in the support graph and `llama-3.1-8b-instant` for low-latency tool calling in the live ingest API.

### Agent Responsibilities
1. **Triage Agent (Gatekeeper):** Parses the order JSON. If critical fields (`item_category`, `order_status`) are missing, it halts the graph entirely (routing to `END`) to ask targeted clarifying questions, preventing the system from guessing.
2. **Retriever Agent (RAG Engine):** Activated only if triage passes. Uses `HuggingFaceEmbeddings` (`all-MiniLM-L6-v2`) and ChromaDB to fetch the top 3 relevant policy chunks based on a combined query of the ticket and order context.
3. **Writer Agent (Drafter):** Formulates the customer response and decision rationale (approve, deny, escalate). It is strictly prompted to include exact citation chunks (e.g., `[Doc: X | Chunk: Y]`) to prove grounding.
4. **Compliance Agent (Auditor):** An adversarial node that reviews the draft against the raw retrieved policies. It catches out-of-policy promises or unauthorized user pressure for exceptions. If it fails the draft, it loops back to the Writer for a rewrite (capped at 3 loops to prevent infinite recursion).

### Data Sources
1. **Policy Vector Store:** A local ChromaDB directory stores embedded chunks of company policies (e.g., return windows, perishable goods exceptions).
2. **Live Inventory API:** The FastAPI app (`ingest.py`) connects to a local Node.js backend to fetch live pricing and product availability.
3. **Fallback Web Search:** A DuckDuckGo search tool is utilized if internal documentation lacks technical product specifications.

### Evaluation Summary & Edge Cases Handled
The system was evaluated against three distinct failure modes. The multi-agent setup successfully isolated them:
* **Perishable Exception:** Correctly identifies a melted item, successfully denies the standard return based on the retrieved perishable policy, and cites the specific rule.
* **Hostile Out-of-Policy Demand:** Rejects a 30+ day return demand from an "influencer." The Compliance agent catches the pressure and flags `escalate: True`.
* **Missing Data Abstention:** Successfully halts execution when the order status is missing, returning a clarifying question instead of hallucinating an answer.

### Key Failure Modes & Mitigations
* **Key Failure Mode 1 (Looping):** Initially, if the Retriever failed to find a policy, the Writer would guess, causing the Compliance agent to reject it and trigger an infinite loop. *Mitigation:* Introduced a `loop_count` state variable that forces an escalation after 3 failed rewrites.
* **Key Failure Mode 2 (Context Ignorance):** Early testing showed the Retriever missing policies if the ticket didn't explicitly mention keywords. *Mitigation:* Fixed by appending the parsed JSON `order_context` directly into the Chroma search query.

### Next Steps & Future Improvements
1. **Human-in-the-Loop (HITL):** Implement LangGraph's native breakpoint features before the final state, allowing human supervisors to manually approve or override rewrites for high-value tickets.
2. **Hybrid Retrieval:** Upgrade the ChromaDB dense retriever to use Hybrid Search (BM25 + Dense Embeddings) to improve policy matching for highly specific SKU queries or exact policy ID numbers.
    F -- Hallucination / Policy Breach --> E
    F -- Out-of-Policy Demand --> G[Escalate to Human]
    F -- 100% Compliant --> H[Final Customer Response]


## 🧠 Architecture Overview

The core resolution engine is a state-machine orchestrated by **LangGraph**, utilizing **Groq's Llama 3.3 70B** for complex reasoning and **ChromaDB** for semantic policy retrieval.

```mermaid
graph TD
    A[Incoming Ticket + Order JSON] --> B{Triage Agent}
    B -- Missing Context --> C[Halt: Ask Clarifying Qs]
    B -- Context Complete --> D[Retriever Agent]
    D --> E[Writer Agent]
    E --> F{Compliance Auditor}

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

***

### 2. The Engineering Write-Up
*Save this as a PDF or Markdown file (e.g., `Architecture_WriteUp.md`) to include with your submission.*

```markdown
# Engineering Write-Up: Multi-Agent Resolution System

### Architecture & Philosophy
The system is built on a state-machine architecture using **LangGraph**, deliberately moving away from naive zero-shot prompting to a deterministic, node-based workflow. By dividing the resolution process into isolated, specialized agents (Triage, Retrieval, Writing, Compliance), the system significantly reduces hallucinations and ensures strict adherence to company guidelines. 

The application utilizes **Groq** to power the Llama 3 models, specifically leveraging `llama-3.3-70b-versatile` for deep reasoning in the support graph and `llama-3.1-8b-instant` for low-latency tool calling in the live ingest API.

### Agent Responsibilities
1. **Triage Agent (Gatekeeper):** Parses the order JSON. If critical fields (`item_category`, `order_status`) are missing, it halts the graph entirely (routing to `END`) to ask targeted clarifying questions, preventing the system from guessing.
2. **Retriever Agent (RAG Engine):** Activated only if triage passes. Uses `HuggingFaceEmbeddings` (`all-MiniLM-L6-v2`) and ChromaDB to fetch the top 3 relevant policy chunks based on a combined query of the ticket and order context.
3. **Writer Agent (Drafter):** Formulates the customer response and decision rationale (approve, deny, escalate). It is strictly prompted to include exact citation chunks (e.g., `[Doc: X | Chunk: Y]`) to prove grounding.
4. **Compliance Agent (Auditor):** An adversarial node that reviews the draft against the raw retrieved policies. It catches out-of-policy promises or unauthorized user pressure for exceptions. If it fails the draft, it loops back to the Writer for a rewrite (capped at 3 loops to prevent infinite recursion).

### Data Sources
1. **Policy Vector Store:** A local ChromaDB directory stores embedded chunks of company policies (e.g., return windows, perishable goods exceptions).
2. **Live Inventory API:** The FastAPI app (`ingest.py`) connects to a local Node.js backend to fetch live pricing and product availability.
3. **Fallback Web Search:** A DuckDuckGo search tool is utilized if internal documentation lacks technical product specifications.

### Evaluation Summary & Edge Cases Handled
The system was evaluated against three distinct failure modes. The multi-agent setup successfully isolated them:
* **Perishable Exception:** Correctly identifies a melted item, successfully denies the standard return based on the retrieved perishable policy, and cites the specific rule.
* **Hostile Out-of-Policy Demand:** Rejects a 30+ day return demand from an "influencer." The Compliance agent catches the pressure and flags `escalate: True`.
* **Missing Data Abstention:** Successfully halts execution when the order status is missing, returning a clarifying question instead of hallucinating an answer.

### Key Failure Modes & Mitigations
* **Key Failure Mode 1 (Looping):** Initially, if the Retriever failed to find a policy, the Writer would guess, causing the Compliance agent to reject it and trigger an infinite loop. *Mitigation:* Introduced a `loop_count` state variable that forces an escalation after 3 failed rewrites.
* **Key Failure Mode 2 (Context Ignorance):** Early testing showed the Retriever missing policies if the ticket didn't explicitly mention keywords. *Mitigation:* Fixed by appending the parsed JSON `order_context` directly into the Chroma search query.

### Next Steps & Future Improvements
1. **Human-in-the-Loop (HITL):** Implement LangGraph's native breakpoint features before the final state, allowing human supervisors to manually approve or override rewrites for high-value tickets.
2. **Hybrid Retrieval:** Upgrade the ChromaDB dense retriever to use Hybrid Search (BM25 + Dense Embeddings) to improve policy matching for highly specific SKU queries or exact policy ID numbers.
    F -- Hallucination / Policy Breach --> E
    F -- Out-of-Policy Demand --> G[Escalate to Human]
    F -- 100% Compliant --> H[Final Customer Response]
