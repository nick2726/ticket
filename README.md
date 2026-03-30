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

