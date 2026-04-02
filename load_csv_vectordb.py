"""
LANGCHAIN VECTOR INGESTION
CSV → Documents → Embeddings → ChromaDB

Recommended for:
- RAG apps
- AI agents
- semantic search
- production pipelines
"""

# =========================
# IMPORTS
# =========================

import os
import glob

# LangChain loaders
from langchain_community.document_loaders import CSVLoader

# LangChain embeddings
from langchain_openai import OpenAIEmbeddings

# LangChain vector DB wrapper
from langchain_community.vectorstores import Chroma

# Optional text splitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config

# =========================
# CONFIG
# =========================

CSV_FOLDER = "data"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "real_estate_collection"

EMBED_MODEL = "text-embedding-3-small"


# =========================
# STEP 1 — FIND CSV FILES
# =========================

csv_files = glob.glob(os.path.join(CSV_FOLDER, "*.csv"))

if not csv_files:
    raise ValueError("No CSV files found.")

print(f"Found {len(csv_files)} CSV files")


# =========================
# STEP 2 — LOAD CSV FILES
# =========================

all_documents = []

# LOOP → iterate through each csv file
for file in csv_files:

    print(f"Loading: {file}")

    # CSVLoader converts each row → LangChain Document
    loader = CSVLoader(file_path=file)

    docs = loader.load()

    # Add filename metadata to each document
    for doc in docs:
        doc.metadata["source_file"] = os.path.basename(file)
        
    # Add loaded docs to master list
    all_documents.extend(docs)

print(f"Total documents loaded: {len(all_documents)}")


# =========================
# STEP 3 — SPLIT DOCUMENTS
# =========================

"""
Why splitting?

If rows contain long text fields:
- description
- remarks
- comments

Splitting improves search accuracy.
"""

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

documents = text_splitter.split_documents(all_documents)

print(f"Total chunks after splitting: {len(documents)}")


# =========================
# STEP 4 — LOAD EMBEDDING MODEL
# =========================

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=config.OPENAI_API_KEY
)

print("Embedding model loaded")


# =========================
# STEP 5 — CREATE VECTOR DB
# =========================

# =========================
# STEP 5 — CREATE / LOAD VECTOR DB
# =========================

"""
Production-safe ingestion logic:

If collection exists → load it
If not → create it
Then add documents
"""

# Load existing DB if present
vector_db = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME
)

# Check existing vector count
existing_count = vector_db._collection.count()
print(f"Existing vectors in DB: {existing_count}")

# Only add if new documents exist
if documents:
    print("Adding documents to vector DB...")
    vector_db.add_documents(documents)
else:
    print("No documents to add.")

# Force persistence to disk
vector_db.persist()

print("\n========================")
print("INGESTION COMPLETE")
print(f"Collection name: {COLLECTION_NAME}")
print(f"Total vectors now: {vector_db._collection.count()}")
print(f"Stored in: {CHROMA_DIR}")
print("========================")
