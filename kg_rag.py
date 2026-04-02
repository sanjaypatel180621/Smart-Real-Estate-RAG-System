"""
KG-RAG using LangChain + Neo4j
- Generates Cypher using LLM
- Cleans Markdown (```cypher)
- Validates Cypher
- Executes safely in Neo4j
"""

import re
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ---------------------------------------------------
# 1. LOAD CONFIG
# ---------------------------------------------------
import config  # must define OPENAI_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# ---------------------------------------------------
# 2. NEO4J CONNECTION
# ---------------------------------------------------
driver = GraphDatabase.driver(
    config.NEO4J_URI,
    auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
)


# ---------------------------------------------------
# 3. CYPHER CLEANER & VALIDATOR
# ---------------------------------------------------
def extract_cypher(llm_output: str) -> str:
    """
    Removes ```cypher / ``` Markdown from LLM output.
    """
    if not llm_output:
        raise ValueError("Empty LLM output")

    cleaned = re.sub(r"```[a-zA-Z]*", "", llm_output)
    cleaned = cleaned.replace("```", "")
    return cleaned.strip()


def validate_cypher(query: str) -> None:
    forbidden = [
        "u.bhk",
        "l-[:HAS_UNIT]",
        "Location)-[:HAS_UNIT]"
    ]

    for f in forbidden:
        if f.lower() in query.lower():
            raise ValueError(f"Invalid Cypher pattern detected: {f}")

    allowed = ("MATCH", "WITH", "CALL")
    if not query.upper().startswith(allowed):
        raise ValueError("Unsafe Cypher generated")

# ---------------------------------------------------
# 4.RESOLVE QUESTION
# ---------------------------------------------------       

# ---------------------------------------------------
# SMART FILTER RESOLVER
# ---------------------------------------------------
def resolve_filters(question: str) -> str:
    """
    Normalize user text so Neo4j values match exactly.
    Prevents empty results due to casing/spacing mismatches.
    """

    mapping = {
        "swimming pool": "Swimming Pool",
        "gym": "Gym",
        "sea view": "Sea View",
        "2 bhk": "2BHK",
        "3 bhk": "3BHK",
        "1 bhk": "1BHK"
    }

    q = question.lower()

    for k, v in mapping.items():
        q = q.replace(k, v)

    return q

# ---------------------------------------------------
# 5. LLM SETUP
# ---------------------------------------------------
llm = ChatOpenAI(
    model= config.OPENAI_MODEL, # ✅ correct model for testing
    api_key=config.OPENAI_API_KEY,
    temperature=0
)

# ---------------------------------------------------
# 5. CYPHER GENERATION PROMPT
# ---------------------------------------------------
CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template="""
You are an expert Neo4j Cypher developer.

Your task:
Generate ONE correct Cypher query for the user's question using ONLY the schema provided.

STRICT RULES:
- Always return only Cypher query — no explanation.
- Always match string values using toLower()
- Do NOT use Markdown or ```
- Do NOT add explanations
- Output must start with MATCH, WITH, or CALL
- Follow the schema EXACTLY
- Use correct relationship directions
- Use UnitType for BHK filtering
- Use BuyerType for buyer filtering
- Use DISTINCT when returning nodes
- Return only relevant fields.
- If filtering strings, match case exactly.
- Use only labels, relationships, and properties from schema.
- Use a single MATCH per path pattern.
- Do not repeat MATCH for same variable.
- Combine conditions on same node inside one pattern.


QUERY RULES:
• If question asks about projects → return Project fields
• If question asks about price → return Unit.price
• If question asks about unit → return Unit fields
• If multiple filters → combine them into same MATCH chain

Schema:
{schema}

Question:
{question}
"""
)

cypher_chain = CYPHER_PROMPT | llm | StrOutputParser()

# ---------------------------------------------------
# 6. SCHEMA (STATIC OR FETCHED)
# ---------------------------------------------------
GRAPH_SCHEMA = """
Nodes:
(:Project {project_id, name, status, launch_year, price_per_sqft})
(:Location {name})
(:Unit {unit_id, size_sqft, price})
(:UnitType {name})
(:BuyerType {name, description})
(:Amenity {name})

Relationships:
(:Project)-[:LOCATED_IN]->(:Location)
(:Project)-[:HAS_UNIT]->(:Unit)
(:Unit)-[:HAS_UNIT_TYPE]->(:UnitType)
(:Unit)-[:TARGETED_FOR]->(:BuyerType)
(:Project)-[:HAS_AMENITY]->(:Amenity)

Rules:
- UnitType.name values are like: 1BHK, 2BHK, 3BHK
- BuyerType.name values are like: Investor, End User
- NEVER assume Location connects directly to Unit
- ALWAYS connect Unit through Project
"""


# ---------------------------------------------------
# 7. EXECUTE CYPHER
# ---------------------------------------------------
def run_cypher(query: str):
    with driver.session(database=config.DB_NAME) as session:
        result = session.run(query)
        return [record.data() for record in result]

# ---------------------------------------------------
# 8. MAIN KG-RAG FUNCTION
# ---------------------------------------------------
def kg_rag(question: str):
    
   
    #1. normalize user input BEFORE sending to LLM
    question = resolve_filters(question)
    print(question)

    #2. LLM generates Cypher
    raw_output = cypher_chain.invoke({
        "schema": GRAPH_SCHEMA,
        "question": question
    })

    # 2. Clean Markdown
    cypher = extract_cypher(raw_output)
    
    # 3. Validate
    validate_cypher(cypher)
      
    #4.Removes newlines,tabs and double spaces :
    cypher = re.sub(r"\s+", " ", cypher).strip()
    print(cypher)
    # 4.. Execute
    results = run_cypher(cypher)
    print("Results from kg_rag:",results)
    confidence = 0.9 if results else 0.0

    return {
    "status": "success" if results else "failed",
    "answer": results if results else "No matching data found in graph.",
    "confidence": confidence,
    "source": "kgrag"
    }
  
    
# ---------------------------------------------------
# 9. EXAMPLE RUN
# ---------------------------------------------------
if __name__ == "__main__":
   #-------------------------------------------------- 
    #q = "Show projects in Velachery with price per sqft above 8000."
    #response = kg_rag(q)
    #print("\nGenerated Cypher:\n", response["cypher"])
    #print("\nResults:",response["answer"])
    pass
#------------------------------------------------------