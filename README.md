# 🏙️ Smart Real Estate RAG System - Intelligence Hybrid RAG Agent (KG RAG + Neo4j + Vector Search + LLM Router)

A Hybrid Retrieval-Augmented Generation (RAG) system for real estate that combines **Knowledge Graph (Neo4j)** and **Vector Search (ChromaDB)** to answer structured, semantic, and hybrid queries about properties, prices, amenities, and locations — powered by OpenAI and served through a Streamlit interface.

---

## Architecture Overview

```
                        ┌──────────────┐
                        │  User Query     │
                        └──────┬───────┘
                               │
                    ┌──────────▼──────────┐
                    │    Smart Router          │
                    │  (Rule + LLM-based).     │
                    └──┬───────┬───────┬──┘
                        │       │       │
              STRUCTURED    HYBRID   SEMANTIC
                       │       │       │
               ┌───────▼──┐   │  ┌────▼────────┐
               │  KG-RAG  │   │  │Corrective RAG│
               │ (Neo4j)  │   │  │ (ChromaDB)   │
               └───────┬──┘   │  └────┬─────────┘
                       │      │       │
                       │  ┌───▼───┐   │
                       └─►│ Merge │◄──┘
                          └───┬───┘
                              │
                     ┌────────▼────────┐
                     │  Streamlit UI   │
                     └─────────────────┘
```

The system intelligently routes each query through a two-stage classifier:

1. **Rule-based classifier** — fast keyword matching for queries with clear numeric filters or recommendation intent.
2. **LLM classifier (fallback)** — uses OpenAI to classify ambiguous queries.

Based on classification, the query is dispatched to one of three paths:

| Intent       | Engine                          | Example Query                                       |
|--------------|---------------------------------|-----------------------------------------------------|
| `STRUCTURED` | Knowledge Graph (Neo4j + Cypher)| *"Show 2BHK units in Velachery under 80 lakhs"*     |
| `SEMANTIC`   | Corrective RAG (ChromaDB)       | *"Which project is best for investment?"*            |
| `HYBRID`     | Both engines, merged via LLM    | *"Recommend 3BHK projects in OMR above 7000/sqft"*  |

---

## Knowledge Graph Schema

The Neo4j graph models the real estate domain with six node types and five relationship types:

```
(:Project)-[:LOCATED_IN]->(:Location)
(:Project)-[:HAS_UNIT]->(:Unit)
(:Project)-[:HAS_AMENITY]->(:Amenity)
(:Unit)-[:HAS_UNIT_TYPE]->(:UnitType)        // 1BHK, 2BHK, 3BHK, Villa
(:Unit)-[:TARGETED_FOR]->(:BuyerType)        // Investor, End User
```

Node properties include `project_id`, `name`, `launch_year`, `price_per_sqft`, `status`, `size_sqft`, `price`, and more.

---

## Corrective RAG Pipeline

The vector search path implements a **Corrective RAG** strategy with self-healing retrieval:

1. **Retrieve** — similarity search over ChromaDB (`text-embedding-3-small`).
2. **Grade relevance** — LLM checks if retrieved documents actually answer the question.
3. **Rewrite (if needed)** — if documents are irrelevant, the query is rewritten and retrieval is retried.
4. **Generate** — final answer is produced grounded strictly in the retrieved context.

If the corrective RAG confidence falls below `0.45`, the system automatically falls back to the Knowledge Graph.

---

## Project Structure

```
RealEstateagent/
├── app.py                  # Streamlit chat interface
├── router.py               # Hybrid query router (rule + LLM classifier)
├── kg_rag.py               # Knowledge Graph RAG (Neo4j + Cypher generation)
├── vector_rag.py           # Corrective Vector RAG (ChromaDB + OpenAI)
├── load_csv_neo4j.py       # CSV → Neo4j graph ingestion script
├── load_csv_vectordb.py    # CSV → ChromaDB vector ingestion script
├── create_constraints.py   # Neo4j uniqueness constraints setup
├── requirements.txt        # Python dependencies
├── chroma_db/              # Persisted ChromaDB vector store
└── data/
    ├── projects_100.csv    # Project details (name, location, price/sqft, status)
    ├── units_100.csv       # Unit details (type, size, price)
    ├── buyers_100.csv      # Buyer type categories
    ├── sales_100.csv       # Sales records linking units to buyers
    ├── amenities_100.csv   # Project amenities (Gym, CCTV, Swimming Pool, etc.)
    └── sample/             # Smaller sample datasets for testing
```

---

## Prerequisites

- **Python 3.10+**
- **Neo4j** (local or Aura cloud instance)
- **OpenAI API key**

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/JeyaAlagappan/Hybrid-Rag.git
   cd Hybrid-Rag/RealEstateagent
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install streamlit openai langchain langchain-openai langchain-chroma langchain-community chromadb
   ```

3. **Configure environment**

   Create a `config.py` file in the project root with the following variables:

   ```python
   NEO4J_URI = "bolt://localhost:7687"
   NEO4J_USER = "neo4j"
   NEO4J_PASSWORD = "your-neo4j-password"
   DB_NAME = "neo4j"

   OPENAI_API_KEY = "sk-your-openai-api-key"
   OPENAI_MODEL = "gpt-4o-mini"

   CHROMA_PATH = "./chroma_db"
   ```

4. **Set up Neo4j constraints**

   ```bash
   python create_constraints.py
   ```

5. **Load data into Neo4j**

   ```bash
   python load_csv_neo4j.py
   ```

6. **Load data into ChromaDB**

   ```bash
   python load_csv_vectordb.py
   ```

---

## Usage

Launch the Streamlit application:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` and start asking questions like:

- *"Show projects in Anna Nagar with price per sqft above 7000"* → routed to **Knowledge Graph**
- *"Which project is the best for long-term investment?"* → routed to **Corrective RAG**
- *"Recommend 2BHK units in OMR under 60 lakhs with a gym"* → routed to **Hybrid** (both engines)

---

## How Routing Works

The `router.py` module implements a layered classification strategy:

```
User Query
    │
    ▼
Rule Classifier ── matches keywords + numbers ──► STRUCTURED / SEMANTIC / HYBRID
    │
    │ (if UNKNOWN)
    ▼
LLM Classifier ── OpenAI classifies intent ──► STRUCTURED / SEMANTIC / HYBRID
    │
    ▼
Engine Dispatch
    │
    ├── STRUCTURED  →  KG-RAG (Cypher generation + Neo4j execution)
    ├── SEMANTIC    →  Corrective RAG (ChromaDB retrieval + relevance grading)
    └── HYBRID      →  Both engines → LLM-powered answer fusion
```

Safety mechanisms are built in at every level: engine calls are wrapped in error handlers, confidence scores are tracked, and fallback paths activate automatically when a primary engine returns weak results.

---

## Dataset

The project ships with synthetic real estate data covering 100 projects across Chennai localities including Tambaram, Anna Nagar, Velachery, OMR, and more. The data spans projects, units (1BHK through Villa), amenities, buyer types, and sales records.

---

## Tech Stack

| Component        | Technology                        |
|------------------|-----------------------------------|
| LLM              | OpenAI (GPT-4o-mini)             |
| Embeddings       | OpenAI `text-embedding-3-small`  |
| Knowledge Graph  | Neo4j                            |
| Vector Store     | ChromaDB                         |
| Orchestration    | LangChain                        |
| Frontend         | Streamlit                        |
| Language         | Python                           |

---

## License

This project is open source. See the repository for license details.

---

## Author

**Sanjay Chintamani Patel** — [Google](https://www.google.com/search?q=sanjay+chintamani+patel)
