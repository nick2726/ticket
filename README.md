# 🚀 JARVIS: Multi-Agent Support & E-Commerce Resolution System

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi) ![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange) ![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-4B32C3) ![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-black)

An end-to-end, multi-agent AI system designed to handle customer support tickets and act as an intelligent e-commerce assistant. Using LangGraph, the system intelligently triages requests, retrieves relevant store policies via RAG, drafts compliance-checked responses, and ensures zero-hallucination policy enforcement—escalating to a human agent only when exactly necessary.


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






