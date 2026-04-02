import config
import os
from openai import OpenAI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


# =========================
# INIT
# =========================

client = OpenAI(api_key=config.OPENAI_API_KEY)

os.makedirs(config.CHROMA_PATH, exist_ok=True)

embedding = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=config.OPENAI_API_KEY
)

vectordb = Chroma(
    collection_name="real_estate_collection",
    embedding_function=embedding,
    persist_directory=config.CHROMA_PATH
)


# =========================
# RETRIEVE DOCS
# =========================

def retrieve_docs(query, k=4):
    docs = vectordb.similarity_search(query, k=k)
    return docs


# =========================
# QUERY REWRITE (CORRECTIVE STEP)
# =========================

def rewrite_query(original_question):

    prompt = f"""
Rewrite this real estate search query to be clearer and more searchable.
Only return rewritten query.

Query:
{original_question}
"""

    res = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content.strip()


# =========================
# DOC RELEVANCE CHECK
# =========================

def grade_relevance(question, docs):

    if not docs:
        return False

    context = "\n".join([d.page_content for d in docs[:3]])

    prompt = f"""
Question:
{question}

Context:
{context}

Are these documents relevant to answer the question?

Reply ONLY with:
YES
or
NO
"""

    res = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    answer = res.choices[0].message.content.strip().upper()

    return "YES" in answer


# =========================
# FINAL ANSWER GENERATION
# =========================

def generate_answer(question, docs):

    context = "\n\n".join([d.page_content for d in docs])

    prompt = f"""
You are a real estate assistant.

Answer ONLY from this context:

{context}

Question:
{question}

If answer not found, say:
"I could not find this in the database."
"""

    res = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content.strip()


# =========================
# CORRECTIVE RAG PIPELINE
# =========================

def ask_rag(question):

    print("\n--- STEP 1: Initial Retrieval ---")
    docs = retrieve_docs(question)

    # STEP 2 — CHECK RELEVANCE
    print("Checking relevance...")
    relevant = grade_relevance(question, docs)

    # STEP 3 — IF NOT RELEVANT → REWRITE QUERY
    if not relevant:
        print("Low relevance detected. Rewriting query...")
        better_query = rewrite_query(question)
        print("Rewritten query:", better_query)

        docs = retrieve_docs(better_query)

        relevant = grade_relevance(question, docs)

        if not relevant:
            return {
                "status": "failed",
                "answer": "No relevant data found in database.",
                "docs": []
            }

    # STEP 4 — GENERATE FINAL ANSWER
    print("Generating final answer...")
    answer = generate_answer(question, docs)
    print(answer)
    # CONFIDENCE SCORE
    confidence = min(1.0, len(docs) / 4)
    #print(confidence)
    return {
    "status": "success",
    "confidence": round(confidence, 2),
    "answer": answer,
    "source": "vector"
    }




# =========================
# MAIN TEST
# =========================

if __name__ == "__main__":

    ##question = "Which projects are available in OMR?"

    #result = ask_rag(question)

    #print("\n================ RESULT ================")
    #print("Status:", result["status"])
    #print("Confidence:", result.get("confidence"))
    #print("Docs Used:", result.get("docs_used"))
    #print("Answer:\n", result["answer"])
    pass
