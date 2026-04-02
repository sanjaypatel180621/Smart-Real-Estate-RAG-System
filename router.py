"""
router.py
Hybrid Router for Real Estate AI Agent

Routing Strategy:
1. Rule-based classifier (fast)
2. LLM classifier fallback
3. Engine selection:
      STRUCTURED -> Graph RAG
      SEMANTIC -> Corrective RAG
      HYBRID -> Both
4. Confidence fallback
5. Safe engine execution wrapper
6. Unified output schema

Author: Hybrid RAG Controller
"""

from neo4j import Result
import config
from openai import OpenAI

# Engines
from vector_rag import ask_rag as corrective_rag
from kg_rag import kg_rag as graph_rag


# =========================
# INIT CLIENT
# =========================
client = OpenAI(api_key=config.OPENAI_API_KEY)


# =========================
# RULE CLASSIFIER
# =========================
def rule_classifier(query: str) -> str:
    """
    Fast keyword classifier.
    Returns:
    STRUCTURED | SEMANTIC | HYBRID | UNKNOWN
    """

    q = query.lower()

    structured_keywords = [
        "under","above","below","less than","greater than",
        "budget","price","sqft","bhk","bedroom",
        "in","near","location","area"
    ]

    semantic_keywords = [
        "best","good","recommend","suggest",
        "better","ideal","should i","worth","investment"
    ]

    has_number = any(char.isdigit() for char in q)

    structured_hit = any(k in q for k in structured_keywords)
    semantic_hit   = any(k in q for k in semantic_keywords)

    # ---------- HYBRID ----------
    if (has_number and structured_hit) and semantic_hit:
        return "HYBRID"

    # ---------- STRUCTURED ----------
    if has_number and structured_hit:
        return "STRUCTURED"

    # ---------- SEMANTIC ----------
    if semantic_hit:
        return "SEMANTIC"

    return "UNKNOWN"

    
# =========================
# LLM CLASSIFIER
# =========================
def llm_classifier(query: str) -> str:

    prompt = f"""
Classify this real estate query.

STRUCTURED → filters or constraints
SEMANTIC → descriptive or recommendation
HYBRID → both

Query:
{query}

Reply ONLY with one word:
STRUCTURED
SEMANTIC
HYBRID
"""

    try:
        res = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        label = res.choices[0].message.content.strip().upper()

        if label not in ["STRUCTURED","SEMANTIC","HYBRID"]:
            return "SEMANTIC"

        return label

    except Exception as e:
        print("LLM classifier failed:", e)
        return "SEMANTIC"


# =========================
# FINAL CLASSIFIER
# =========================
def classify_query(query: str) -> str:

    rule = rule_classifier(query)

    if rule != "UNKNOWN":
        print("Rule classifier →", rule)
        return rule

    print("Rule uncertain → using LLM classifier")
    return llm_classifier(query)


# =========================
# SAFE ENGINE EXECUTION
# =========================
def safe_engine_call(engine, question, name):
    """
    Executes any engine safely and normalizes output schema.
    """

    try:
        result = engine(question)

        if not isinstance(result, dict):
            raise ValueError("Engine returned non-dict output")

        if "answer" not in result:
            raise ValueError("Missing 'answer' key")

        return {
            "status": "success",
            "answer": result["answer"],
            "confidence": result.get("confidence", 0.7),
            "source": name
        }

    except Exception as e:

        print(f"{name} ENGINE ERROR:", e)

        return {
            "status": "failed",
            "answer": None,
            "confidence": 0,
            "source": name,
            "error": str(e)
        }


# =========================
# MERGE ANSWERS
# =========================
def merge_answers(question, graph_answer, rag_answer):

    prompt = f"""
You are a real estate assistant.

Combine both answers into one final helpful response.

Graph Answer:
{graph_answer}

RAG Answer:
{rag_answer}

Question:
{question}
"""

    res = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role":"user","content":prompt}]
    )

    return res.choices[0].message.content.strip()


# =========================
# ROUTER CORE
# =========================
def route_query(question: str):

    print("\n========== ROUTER ==========")
    print("Question:", question)

    intent = classify_query(question)
    print("Intent:", intent)


    # =======================
    # STRUCTURED → GRAPH
    # =======================
    if intent == "STRUCTURED":

        graph = safe_engine_call(graph_rag, question, "GRAPH")
        
        return {
            "route": "GRAPH",
            **graph
        }

        #print("Result from route:",graph)

    # =======================
    # SEMANTIC → RAG
    # =======================
    elif intent == "SEMANTIC":

        rag = safe_engine_call(corrective_rag, question, "CORRECTIVE_RAG")

        # fallback if weak or failed
        if rag["confidence"] < 0.45 or rag["status"] == "failed":

            print("Low confidence → fallback to graph")

            graph = safe_engine_call(graph_rag, question, "GRAPH_FALLBACK")

            return {
                "route": "GRAPH_FALLBACK",
                **graph
            }

        return {
            "route": "CORRECTIVE_RAG",
            **rag
        }


    # =======================
    # HYBRID → BOTH
    # =======================
    else:

        graph = safe_engine_call(graph_rag, question, "GRAPH")
        rag   = safe_engine_call(corrective_rag, question, "RAG")

        # if one fails → return other
        if graph["status"] == "failed":
            return {
                "route":"RAG_ONLY",
                **rag
            }

        if rag["status"] == "failed":
            return {
                "route":"GRAPH_ONLY",
                **graph
            }

        merged = merge_answers(
            question,
            graph["answer"],
            rag["answer"]
        )

        avg_conf = (graph["confidence"] + rag["confidence"]) / 2

        return {
            "status":"success",
            "route":"HYBRID",
            "answer": merged,
            "confidence": round(avg_conf,2),
            "source":"fusion"
        }


# =========================
# CLI TEST
# =========================
if __name__ == "__main__":

    #q = "Show projects in Velachery with price per sqft above 8000"

    #result = route_query(q)
    
    #print(result)

    #print("\n=========== RESULT ===========")
    #print("Route:", result["route"])
    #print("Confidence:", result["confidence"])
    #print("Answer:\n", result["answer"])
    pass
