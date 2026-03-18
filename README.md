# 🧠 Local AI CLI Chatbot

A local-first AI chatbot built with Python, LM Studio, and SQLite.

---

## 📌 Project Status

🚧 This project is currently under active development.

The current version focuses on:

- connecting a Python CLI app to a locally hosted LLM via LM Studio
- storing chat history in SQLite
- maintaining a clean and extensible project structure

---

## 📖 Overview

This project is a local AI chatbot that runs on your machine and communicates with a locally hosted language model via an OpenAI-compatible API provided by LM Studio.

Key characteristics:

- local LLM inference through LM Studio  
- persistent chat history using SQLite  
- no dependency on third-party cloud LLM APIs  
- designed as a foundation for future AI features such as retrieval and RAG  

---

## 🏗️ Architecture

```text
User Input
   ↓
Python CLI (app.py)
   ↓
LM Studio (local API server)
   ↓
Local LLM response
   ↓
SQLite (chat history)
```

---

## 📁 Project Structure

```text
.
├── app.py
├── config.py
├── db.py
├── data/                # runtime data (not tracked by Git)
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

---

## ⚙️ Configuration

Environment variables are managed via `.env`.

### Step 1: Create `.env`

```bash
cp .env.example .env
```

### Step 2: Configure values

```env
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
MODEL_NAME=qwen2.5-7b-instruct
DB_PATH=data/chat_store.db
SESSION_ID=default
```

### Variable Explanation

- **OPENAI_BASE_URL**  
  Local OpenAI-compatible endpoint exposed by LM Studio

- **OPENAI_API_KEY**  
  Placeholder value required by the OpenAI client

- **MODEL_NAME**  
  The model name served by LM Studio

- **DB_PATH**  
  Path to the local SQLite database

- **SESSION_ID**  
  Identifier for the current chat session

---

## 🧩 Tech Stack

- Python  
- OpenAI Python SDK (OpenAI-compatible API)  
- LM Studio  
- SQLite  
- python-dotenv  

---

## 💾 Data Handling

- Chat history is stored locally in:

  ```
  data/chat_store.db
  ```

- The `data/` directory is treated as runtime data and excluded from version control.

---

## 🔐 Privacy

- All inference is performed locally through LM Studio  
- Chat data is stored locally in SQLite  
- No third-party cloud LLM service is required  

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start LM Studio

- Load your model in LM Studio  
- Start the local server (default: http://localhost:1234)  

### 3. Run the chatbot

```bash
python app.py
```

---

## 🎯 Development Roadmap

Planned improvements:

- [ ] Verify and improve LM Studio integration  
- [ ] Improve error handling  
- [ ] Support multi-session chat  
- [ ] Add streaming responses  
- [ ] Add embeddings and retrieval  
- [ ] Evolve into a local RAG system  

---

## 📝 Learning Goal

This project is part of a learning path toward becoming an **AI Application Engineer**, focusing on:

- local-first AI systems  
- practical LLM integration  
- clean software architecture  
- real-world AI application development  
