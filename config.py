import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "local-model")
BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
DB_PATH = os.getenv("DB_PATH", "data/chat_store.db")
SESSION_ID = os.getenv("SESSION_ID", "default")

# Ensure data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)