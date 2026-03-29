import os
import json
from typing import TypedDict, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.graph import StateGraph, END

# 1. Load Environment Variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    print("🔴 ERROR: GROQ_API_KEY is missing from .env file!")

# Change this line at the top of your agent.py file:
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)

# ==========================================
# 2. DEFINE STRUCTURED OUTPUTS (Pydantic)
# ==========================================
class TriageOutput(BaseModel):
    issue_type: str = Field(description="Classification: refund, shipping, payment, promo, fraud, other")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    needs_more_info: bool = Field(description="True ONLY IF crucial order context is missing to make a policy decision")
    clarifying_questions: List[str] = Field(description="List of questions. CRITICAL: If needs_more_info is false, this MUST be an empty list [].")
class WriterOutput(BaseModel):
    decision: str = Field(description="approve, deny, partial, or needs escalation")
    rationale: str = Field(description="Policy-based explanation for the decision")
    citations: List[str] = Field(description="Bullet list with doc + section/chunk id")
    customer_response: str = Field(description="Customer-ready message")
    next_steps: str = Field(description="Internal notes on what support should do next")

class ComplianceOutput(BaseModel):
    passed: bool = Field(description="True if the draft uses ONLY retrieved evidence with zero hallucinations")
    escalate: bool = Field(description="True if user is pressuring for out-of-policy exception")
    feedback: str = Field(description="Critique given back to the writer if passed is false")

# ==========================================
# 3. DEFINE THE LANGGRAPH STATE
# ==========================================
class SupportState(TypedDict):
    ticket_text: str
    order_context: str
    issue_type: str
    confidence: float
    needs_more_info: bool
    clarifying_questions: List[str]
    retrieved_context: str
    decision: str
    rationale: str
    citations: List[str]
    customer_response: str
    next_steps: str
    compliance_passed: bool
    escalate: bool
    compliance_feedback: str
    loop_count: int

def triage_agent(state: SupportState):
    print("➡️ [NODE 1] Triage Agent analyzing ticket...")
    triage_llm = llm.with_structured_output(TriageOutput)
    
    prompt = f"""You are a Support Triage Agent.
    Ticket: {state['ticket_text']}
    Order Context: {state['order_context']}
    
    Classify the issue. 
    1. Read the Order Context JSON carefully. 
    2. If 'item_category' OR 'order_status' is MISSING from the JSON, set needs_more_info to true and ask for it.
    3. If BOTH are present in the JSON (like 'electronics' and 'delivered'), you MUST set needs_more_info to false and clarifying_questions to [].
    4. Never ask for proof or photos.
    """
    result = triage_llm.invoke(prompt)
    
    return {
        "issue_type": result.issue_type,
        "confidence": result.confidence,
        "needs_more_info": result.needs_more_info,
        "clarifying_questions": result.clarifying_questions,
        "decision": "needs info" if result.needs_more_info else "",
        "customer_response": " ".join(result.clarifying_questions) if result.needs_more_info else "",
        "loop_count": 0
    }

def policy_retriever_agent(state: SupportState):
    print("➡️ [NODE 2] Retriever Agent fetching policy documents...")
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        
        # Including the order context ensures it searches for "perishable" or "electronics" policies!
        query = f"{state['ticket_text']} {state['order_context']}"
        docs = retriever.invoke(query)
        
        context_str = "\n".join([f"CITATION: [Doc: {d.metadata.get('source')} | Chunk: {d.metadata.get('chunk_id')}]\nTEXT: {d.page_content}\n" for d in docs])
        return {"retrieved_context": context_str if context_str else "No policies found."}
    except Exception as e:
        return {"retrieved_context": f"System Error: {e}"}

def resolution_writer_agent(state: SupportState):
    print(f"➡️ [NODE 3] Writer Agent drafting response (Attempt {state.get('loop_count', 0) + 1})...")
    writer_llm = llm.with_structured_output(WriterOutput)
    
    prompt = f"""You are a Customer Support Writer.
    Ticket: {state['ticket_text']}
    Context: {state['order_context']}
    Policies: {state['retrieved_context']}
    Previous Compliance Feedback: {state.get('compliance_feedback', 'None')}
    
    CRITICAL RULES:
    1. If the item is 'perishable', you MUST 'deny' the request and cite the specific exception policy.
    2. If the user demands a refund outside the 30-day window, you MUST 'deny' or 'escalate' and cite the standard return policy.
    3. ALWAYS include the exact [Doc: X | Chunk: Y] in your citations list. Do not invent policies.
    """
    result = writer_llm.invoke(prompt)
    
    return {
        "decision": result.decision,
        "rationale": result.rationale,
        "citations": result.citations,
        "customer_response": result.customer_response,
        "next_steps": result.next_steps,
        "loop_count": state.get("loop_count", 0) + 1
    }

def compliance_agent(state: SupportState):
    print("➡️ [NODE 4] Compliance Agent verifying citations...")
    compliance_llm = llm.with_structured_output(ComplianceOutput)
    
    prompt = f"""You are a strict Compliance Auditor. Review the Draft against the Policies.
    Draft Rationale: {state['rationale']}
    Draft Message: {state['customer_response']}
    Provided Policies: {state['retrieved_context']}
    
    RULES:
    1. If the Draft promises ANYTHING not explicitly written in the Policies -> passed: False.
    2. If the user is pressuring for an out-of-policy exception -> escalate: True.
    3. If the draft contains fabricated information -> passed: False.
    """
    result = compliance_llm.invoke(prompt)
    
    return {
        "compliance_passed": result.passed,
        "escalate": result.escalate,
        "compliance_feedback": result.feedback
    }

# ==========================================
# 5. BUILD THE LANGGRAPH ORCHESTRATION
# ==========================================
def triage_router(state: SupportState):
    """Routes to END if info is missing, else proceeds to Retriever."""
    if state["needs_more_info"]:
        print("🛑 TRIAGE: Missing info. Halting to ask customer.")
        return "end"
    return "retriever"

def compliance_router(state: SupportState):
    """Forces rewrite or triggers abstain/escalation path."""
    if state["escalate"] or state["compliance_passed"] or state["loop_count"] >= 3:
        return "end"
    print(f"🔄 COMPLIANCE FAILED: {state['compliance_feedback']}. Routing back to Writer...")
    return "rewrite"

workflow = StateGraph(SupportState)
workflow.add_node("triage", triage_agent)
workflow.add_node("retriever", policy_retriever_agent)
workflow.add_node("writer", resolution_writer_agent)
workflow.add_node("compliance", compliance_agent)

workflow.set_entry_point("triage")
# Add the conditional route from Triage!
workflow.add_conditional_edges("triage", triage_router, {"end": END, "retriever": "retriever"})
workflow.add_edge("retriever", "writer")
workflow.add_edge("writer", "compliance")
workflow.add_conditional_edges("compliance", compliance_router, {"end": END, "rewrite": "writer"})

support_agent = workflow.compile()

# ==========================================
# 6. RUN EVALUATION TEST SET
# ==========================================
def print_output(state):
    print("\n" + "="*50)
    print("REQUIRED ASSESSMENT OUTPUT FORMAT")
    print("="*50)
    print(f"1. Classification:      {state.get('issue_type')} (Confidence: {state.get('confidence')})")
    print(f"2. Clarifying Qs:       {state.get('clarifying_questions', [])}")
    print(f"3. Decision:            {state.get('decision')}")
    print(f"4. Rationale:           {state.get('rationale', 'N/A')}")
    print(f"5. Citations:           {state.get('citations', [])}")
    print(f"6. Customer Response:   {state.get('customer_response')}")
    print(f"7. Next Steps:          {state.get('next_steps', 'Wait for customer')}")
    print("="*50 + "\n")

if __name__ == "__main__":
    # Assessment Requirement: Provide 3 full example runs 
    tests = [
        {
            "name": "1. Exception Handled Correctly (Perishable)",
            "ticket": "My order arrived late and the cookies are melted. I want a full refund and to keep the item.",
            "context": '{"order_date": "2023-10-01", "item_category": "perishable", "order_status": "delivered"}'
        },
        {
            "name": "2. Conflict Handled with Escalation (Not in policy)",
            "ticket": "I know it's past 30 days but I demand a refund for this TV because I am an influencer!",
            "context": '{"order_date": "2023-01-01", "item_category": "electronics", "order_status": "delivered"}'
        },
        {
            "name": "3. Correct Abstention / Need More Info Path",
            "ticket": "I need to return the shirt I bought yesterday.",
            "context": '{}' # Missing order_status and item_category
        }
    ]

    for test in tests:
        print(f"\n\n🚀 RUNNING TEST: {test['name']}")
        final_state = support_agent.invoke({
            "ticket_text": test["ticket"], 
            "order_context": test["context"], 
            "loop_count": 0
        })
        print_output(final_state)
