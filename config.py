import os
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "local-model")
BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
DB_PATH = os.getenv("DB_PATH", "data/chat_store.db")
SESSION_ID = os.getenv("SESSION_ID", "default")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5")
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "knowledge")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")
RAG_COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "knowledge_base")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# Ensure the database directory exists before runtime
db_dir = os.path.dirname(DB_PATH)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

# Ensure the Chroma persistence directory exists before runtime
if CHROMA_PERSIST_DIR:
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Ensure the knowledge directory exists before runtime
if KNOWLEDGE_DIR:
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
