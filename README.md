# 🎥 [Demo Video – Click to Watch] https://drive.google.com/file/d/1ymU8pBw0Q_qOfHyfjn-aMrjgYE44F0qP/view?usp=sharing

---

# 🤖 AI Customer Support Bot  
**A FastAPI + Next.js powered intelligent customer support assistant** that answers FAQs, maintains chat context, and auto-escalates unresolved issues using **OpenAI** and **LangChain**.

---

## 📋 Overview  

This project simulates a **real-world AI-driven customer support chatbot**.  
It combines **FastAPI** (backend) and **Next.js** (frontend) to create a full-stack application where users can chat with an AI assistant that:

- Understands and responds naturally using **OpenAI GPT models**
- Retrieves relevant FAQs
- Maintains context throughout the chat
- Auto-escalates queries requiring human attention
- Summarizes chat sessions using LLMs

---

## 🚀 Features  

| Feature | Description |
|----------|-------------|
| 💬 Conversational Chat | Natural, context-aware AI conversation |
| 🗂️ FAQ Retrieval | Retrieves relevant answers from stored FAQs |
| ⚠️ Escalation Detection | Auto-detects high-risk keywords like “refund”, “cancel”, “angry” |
| 🧠 Context Memory | Session-aware interactions with history retention |
| 🧾 Summarization | Generates session summaries |
| 🗃️ SQLite Database | Persistent session + message tracking |
| 🌐 Frontend UI | Responsive chat interface (Next.js + TailwindCSS) |
| 🔐 Secure Config | Environment variable-based configuration |

---

## 🏗️ Project Structure  

```
ai-cs-bot/
│
├── backend/                 
│   ├── app/
│   │   ├── main.py              # FastAPI routes (sessions, message, summarize)
│   │   ├── llm_client.py        # OpenAI integration + escalation logic
│   │   ├── faq.py               # FAQ search / embeddings
│   │   ├── database.py          # SQLite + SQLAlchemy setup
│   │   ├── models.py            # ORM models
│   │   ├── crud.py              # CRUD functions
│   │   ├── schemas.py           # Pydantic schemas
│   │   └── seed_faq.py          # Seeds sample FAQ entries
│   ├── ai-cs-bot.db             # SQLite database
│   ├── .env                     # Environment variables
│   └── requirements.txt         # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── api/client.ts     # Frontend API client
│   │   │   └── page.tsx          # Chat page
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── Composer.tsx
│   │   │   └── MessageBubble.tsx
│   ├── .env.local               # Frontend API base
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── README.md
└── video.mp4                    # Demo recording (optional)
```

---

## ⚙️ Setup Instructions  

### 🧩 Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn
- Git
- OpenAI API key

---

### 🖥️ Backend Setup (FastAPI)

```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate      # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

#### 🧠 Environment Variables  
Create a `.env` file in `/backend`:
```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
DB_URL=sqlite:///./ai-cs-bot.db
CONTEXT_WINDOW=8
```

#### 🚀 Run the Backend
```bash
uvicorn app.main:app --reload --port 8000
```

Now open your browser at:  
👉 **http://127.0.0.1:8000/docs** (Swagger UI)

---

### 💻 Frontend Setup (Next.js)
```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
npm install
```

Create `.env.local`:
```env
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

Run the frontend:
```bash
npm run dev
```

Access the UI at → **http://localhost:3000**

---

## 🧪 How to Test  

1. Start both backend (`uvicorn`) and frontend (`npm run dev`)
2. Go to **http://localhost:3000**
3. Chat examples:
   - “How do I reset my password?”
   - “I want a refund please.”
4. Observe:
   - AI responds contextually
   - “⚠️ Escalation recommended” appears for critical queries
5. Click **Summarize** → view conversation summary  

---

## 🧠 Escalation Logic  

Inside `llm_client.py`, the system checks for **high-risk keywords** such as:

```python
HIGH_RISK_KEYWORDS = ["refund", "angry", "cancel", "complaint", "not working", "fraud"]
```

If any keyword is detected, the bot will return an escalation message:

> ⚠️ Escalation recommended — please contact support@example.com for further assistance.

---

## 🧾 API Endpoints  

| Method | Endpoint | Description |
|--------|-----------|-------------|
| `POST` | `/sessions` | Create new user session |
| `POST` | `/message` | Send user message → get AI response |
| `POST` | `/sessions/{id}/summarize` | Summarize entire chat session |
| `GET` | `/faq/search` | Get relevant FAQ entries |

---

## 🧰 Tech Stack  

| Layer | Technologies Used |
|--------|------------------|
| **Frontend** | Next.js (TypeScript), React, TailwindCSS |
| **Backend** | FastAPI, Python, SQLAlchemy |
| **Database** | SQLite |
| **AI/LLM** | OpenAI GPT-4o-mini |
| **Prompt Handling** | LangChain |
| **Hosting Options** | Uvicorn (backend), Vercel/Netlify (frontend) |

---

## 📊 Database Schema (Simplified)

| Table | Purpose |
|--------|----------|
| `sessions` | Stores user session info |
| `messages` | Logs conversation messages |
| `faqs` | Stores FAQs + embeddings for similarity search |

---

## 🧾 Deliverables Checklist  

- ✅ AI-powered FAQ & support chatbot  
- ✅ FastAPI backend with context memory  
- ✅ SQLite database for persistent sessions  
- ✅ Escalation detection system  
- ✅ Summarization endpoint  
- ✅ Polished Next.js frontend UI  
- ✅ README documentation + demo video  

---

## 💡 Example Prompts  

- “How do I check my order status?”
- “I need a refund for my purchase.”
- “I can’t log in to my account.”
- “Cancel my order immediately.”

---

## 📜 License  
This project is licensed under the **MIT License**.  
Free to use for educational and research purposes.

---

## 👨‍💻 Author  

**Shahishnu J R**  
📧 [GitHub Profile](https://github.com/shahishnujr)  
💡 AI • Full Stack • Research Enthusiast  

---
