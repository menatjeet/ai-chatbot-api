# ApexAI - Production AI Chatbot API & Interactive Client

[![FastAPI](https://img.shields.io/badge/FastAPI-0.162.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-psycopg3-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Interactions%20API-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-red.svg)](https://alembic.sqlalchemy.org/)
[![Pytest](https://img.shields.io/badge/Tests-29%20Passing-success.svg?logo=pytest&logoColor=white)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A high-performance, asynchronous REST & SSE API for conversational AI applications. Built with **FastAPI**, **PostgreSQL** (via **SQLAlchemy 2.0** & **psycopg 3**), **Alembic**, and the **Google Gemini Interactions API**, featuring stateful conversation memory, secure JWT authentication with Argon2 password hashing, and real-time token streaming over Server-Sent Events (SSE).

Includes a built-in modern, glassmorphic interactive web chat interface at `/chat` and interactive Swagger OpenAPI documentation at `/docs`.

---

## 🌟 Architecture & Key Features

```mermaid
graph TD
    Client["Web Client / Frontend / cURL"]
    
    subgraph FastAPI Application
        Auth["Auth Router (JWT + Argon2)"]
        Conv["Conversations Router"]
        Msg["Messages Router"]
        SSE["SSE Streaming Engine"]
        UI["Interactive UI (/chat)"]
    end

    subgraph Data & Cloud Services
        PG[("PostgreSQL Database (Users, Chats, Messages)")]
        Gemini["Google Gemini API (Interactions API / Memory)"]
    end

    Client -->|Bearer Token & REST| Auth
    Client -->|CRUD Chats| Conv
    Client -->|Sync / Async Messages| Msg
    Client -->|Text/Event-Stream| SSE
    Client -->|Browser GUI| UI

    Auth --> PG
    Conv --> PG
    Msg --> PG
    Msg --> Gemini
    SSE --> Gemini
    SSE --> PG
```

- **Stateless & Stateful Multi-Turn Conversations**: Utilizes the Google Gemini Interactions API (`interaction_id`) persisted alongside chat history for persistent contextual memory.
- **Real-Time Token Streaming (SSE)**: Streams generated AI tokens directly to clients using Server-Sent Events (`text/event-stream`), updating the database upon completion.
- **Enterprise-Grade Security**:
  - Passwords hashed with `Argon2` using `pwdlib`.
  - Stateless authentication via `PyJWT` with configurable HMAC-SHA256 expiration.
  - Multi-tenant data isolation: users can only access and manipulate their own conversations and messages.
- **Relational Data Integrity**: SQLAlchemy 2.0 mapped models with cascading deletions (`users` &rarr; `conversations` &rarr; `messages`).
- **Database Migrations with Alembic**: Fully automated schema versioning ready for fresh deployments or continuous integration.
- **Complete Test Coverage**: 29 unit and integration tests using `pytest` and an isolated in-memory SQLite engine.
- **Interactive Web Interface**: Beautiful, responsive, dark-mode glassmorphic client served natively at `/chat`.

---

## 🚀 Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Framework** | FastAPI 0.162 | High performance asynchronous Python web framework |
| **Language** | Python 3.12 | Modern type hinting and asynchronous coroutines |
| **Database** | PostgreSQL + SQLAlchemy 2.0 | Async-ready ORM with psycopg 3 driver |
| **Migrations** | Alembic | Database schema version control |
| **AI Model** | Google Gemini (google-genai SDK) | Interactions API with multi-turn memory |
| **Security** | Argon2 + PyJWT | Modern password hashing and signed bearer tokens |
| **Streaming** | Server-Sent Events (SSE) | Low-latency token generation streaming |
| **Testing** | Pytest + Starlette TestClient | 29 unit and integration test suite |
| **Deployment** | Render | Ready for free-tier Web Service + Postgres deployment |

---

## 📡 API Reference

Interactive Swagger documentation is available at `/docs` (and ReDoc at `/redoc`).

### 1. Health & Status
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API status, version, and links | No |
| `GET` | `/health` | Basic liveness probe | No |
| `GET` | `/db-check` | Database connectivity probe | No |
| `GET` | `/chat` | Interactive Chatbot GUI | No |

### 2. Authentication (`/api/auth`)
| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new user account | `201 Created` |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT token | `200 OK` |
| `GET` | `/api/auth/me` | Fetch authenticated user profile | `200 OK` |

### 3. Conversations (`/api/conversations`)
| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/conversations/` | Create a new conversation | `201 Created` |
| `GET` | `/api/conversations/` | List user's conversations (descending) | `200 OK` |
| `GET` | `/api/conversations/{id}` | Retrieve specific conversation | `200 OK` |
| `PATCH` | `/api/conversations/{id}` | Rename/update conversation title | `200 OK` |
| `DELETE`| `/api/conversations/{id}` | Delete conversation & cascading messages | `204 No Content` |

### 4. Messages (`/api/conversations/{id}/messages`)
| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `POST` | `/{id}/messages` | Send message and receive full AI reply | `201 Created` |
| `POST` | `/{id}/messages/stream` | Send message and stream AI tokens via SSE | `200 OK` |
| `GET` | `/{id}/messages` | Retrieve conversation message history | `200 OK` |

---

## 💻 Local Setup & Development

### Prerequisites
- Python 3.12+
- PostgreSQL database (or SQLite for development)
- Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/menatjeet/ai-chatbot-api.git
cd ai-chatbot-api

# Create and activate virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

Edit `.env`:
```env
APP_NAME="AI Chatbot API"
APP_VERSION="1.0.0"
DEBUG=True

GEMINI_API_KEY="your-gemini-api-key"
DATABASE_URL="postgresql+psycopg://username:password@localhost:5432/chatbot_db"
JWT_SECRET_KEY="generate-a-secure-random-32-byte-secret"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. Run Database Migrations
```bash
alembic upgrade head
```

### 5. Start the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Open [http://localhost:8000/chat](http://localhost:8000/chat) to use the interactive web client.
- Open [http://localhost:8000/docs](http://localhost:8000/docs) to explore the OpenAPI documentation.

---

## 🧪 Running Automated Tests

The repository includes a comprehensive 29-test test suite covering authentication, conversations, message handling, SSE streaming, error conditions, and cryptographic functions. Tests run against an isolated in-memory SQLite database and do not consume Gemini API credits.

```bash
pytest -v
```

Output:
```text
tests/test_auth.py::test_register_user_success PASSED
tests/test_auth.py::test_register_duplicate_email PASSED
tests/test_auth.py::test_login_success PASSED
tests/test_conversations.py::test_create_conversation PASSED
tests/test_conversations.py::test_conversation_user_isolation PASSED
tests/test_messages.py::test_create_message_success PASSED
tests/test_messages.py::test_stream_message_success PASSED
tests/test_security.py::test_password_hashing PASSED
tests/test_security.py::test_jwt_token_generation PASSED
============================= 29 passed in 3.23s ==============================
```

---

## ☁️ Deploying on Render

This repository is pre-configured with a Render Blueprint (`render.yaml`), `Procfile`, and `build.sh` for seamless 1-click deployment.

### Method 1: Blueprint Deployment (Recommended)
1. Push your repository to GitHub.
2. Log into [Render](https://render.com) and click **New +** &rarr; **Blueprint**.
3. Select your GitHub repository `ai-chatbot-api`.
4. Render will detect `render.yaml` and configure:
   - **PostgreSQL Database** (`ai-chatbot-db`)
   - **Web Service** (`ai-chatbot-api`)
   - Auto-generated `JWT_SECRET_KEY`
5. Under Environment Variables for the Web Service, enter your `GEMINI_API_KEY`.
6. Click **Apply**. Render will automatically run `build.sh` (which installs packages and runs `alembic upgrade head`) and start the app!

### Method 2: Manual Web Service Setup on Render
1. **Create PostgreSQL Database on Render**:
   - Go to Render Dashboard &rarr; **New +** &rarr; **PostgreSQL**.
   - Name: `ai-chatbot-db`
   - Plan: **Free**.
   - Copy the **Internal Database URL**.
2. **Create Web Service on Render**:
   - Go to Render Dashboard &rarr; **New +** &rarr; **Web Service**.
   - Connect your GitHub repository.
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh` (or `pip install -r requirements.txt && alembic upgrade head`)
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Set Environment Variables in Render**:
   | Variable | Value |
   | :--- | :--- |
   | `DATABASE_URL` | Paste your Render PostgreSQL Connection URL |
   | `GEMINI_API_KEY` | Your Google Gemini API Key |
   | `JWT_SECRET_KEY` | Random 32+ character hex string |
   | `PYTHON_VERSION` | `3.12.10` |
4. Click **Deploy Web Service**. Once deployed, your chatbot is live at:
   - Web Chat UI: `https://<your-service>.onrender.com/chat`
   - API Docs: `https://<your-service>.onrender.com/docs`

---

## 🛡️ License

This project is licensed under the MIT License.
