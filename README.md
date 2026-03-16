# AI CLI Chatbot

A simple command-line chatbot built with Python and an LLM API.

This project is the first step in learning AI Application Engineering.  
It demonstrates how a software application can interact with a Large Language Model (LLM) through an API to generate responses.

---

# Project Goal

The goal of this project is to understand the basic workflow of an AI-powered application:

1. Accept user input  
2. Send a request to an LLM API  
3. Receive an AI-generated response  
4. Display the response in the terminal  

This project focuses on the core interaction pattern between an application and an LLM.

---

# Tech Stack

- Python  
- OpenAI-compatible API  
- python-dotenv  

---

# Features

- Command-line chatbot interface  
- Sends user prompts to an LLM  
- Displays AI-generated responses  
- Uses environment variables for API key management  
- Basic prompt structure with system and user roles  

---

# Project Structure

ai-cli-chatbot/

├── ai_chat.py  
├── requirements.txt  
├── .gitignore  
└── README.md  

---

# Setup

## 1 Install dependencies

pip install -r requirements.txt

---

## 2 Create a .env file

Create a file named `.env` in the project root:

OPENAI_API_KEY=your_api_key_here  
OPENAI_BASE_URL=your_api_base_url_here  
MODEL_NAME=your_model_name_here  

Example:

OPENAI_API_KEY=sk-xxxx  
OPENAI_BASE_URL=https://api.openai.com/v1  
MODEL_NAME=gpt-4o-mini  

---

## 3 Run the chatbot

python ai_chat.py

Example interaction:

AI CLI Chatbot started.

You: explain docker  
AI: Docker is a platform that allows developers to package applications into containers...

---

# How It Works

The application follows this flow:

User Input  
↓  
Python Application  
↓  
LLM API Request  
↓  
AI Generated Response  
↓  
Display in Terminal  

---

# Learning Outcomes

This project helps understand:

- What a Large Language Model (LLM) is  
- How applications call an LLM API  
- The structure of AI prompts  
- The role of system and user messages  
- Basic AI application architecture  

---

# Future Improvements

Possible upgrades:

- Add conversation history (memory)  
- Support streaming responses  
- Add configuration options  
- Build a web interface  
- Extend to a RAG-based chatbot  

---

# License

This project is for educational purposes.