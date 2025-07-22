# SignAware AI

AI-powered legal document analysis and PII masking service built with FastAPI, SQLAlchemy, PostgreSQL, and LangChain. Features comprehensive user management, document handling, and intelligent chat capabilities.

## Features

### 👤 User Management

- User accounts with role-based access (customer, legal_advisor, admin)
- Google OAuth integration support
- Email verification and password reset functionality
- Secure user data handling

### 📋 Document Management

- Upload and manage legal documents (Terms of Service, Privacy Policies, Contracts, etc.)
- Document status tracking (pending, processing, completed, failed)
- File metadata storage and management
- Document versioning and history

### 🔒 PII Masking

- Mask personally identifiable information using locally running Deepseek-R1:8B model on Ollama
- Skips thinking steps for clean, direct masked output
- Works with both raw text and stored documents
- Preserves document structure while protecting sensitive data

### 📊 Document Analysis

- Comprehensive legal document analysis using OpenAI GPT-4
- Extracts summaries, hidden clauses, risk assessments, loopholes, and red flags
- Calculates risk scores (1-5) and confidence ratings (0-100%)
- Stores results in PostgreSQL with JSONB for efficient querying
- Structured output using Pydantic models

### 💬 Intelligent Chat Bot

- Context-aware chat using analyzed documents as source of truth
- Conversation history stored in database with session management
- Server-Sent Events (SSE) for real-time streaming responses
- Multiple chat sessions per document
- Message threading and history retrieval

## Tech Stack

- **Framework**: FastAPI with automatic OpenAPI documentation
- **Package Manager**: uv for fast dependency management
- **Database**: PostgreSQL with SQLAlchemy ORM and UUID support
- **AI/ML**: LangChain, OpenAI GPT-4, Ollama (Deepseek-R1:8B)
- **Streaming**: Server-Sent Events with sse-starlette
- **State Management**: LangGraph with PostgreSQL checkpointers

## Database Schema

The application uses a PostgreSQL database with the following main tables:

- **users**: User accounts with authentication and profile information
- **documents**: Legal documents with content, metadata, and analysis results
- **chat_messages**: Chat conversations linked to documents and users

## Prerequisites

1. **Python 3.11+**
2. **PostgreSQL** database server with uuid-ossp extension
3. **Ollama** with Deepseek-R1:8B model installed
4. **OpenAI API Key**

### Install Ollama and Deepseek-R1:8B

```bash
# Install Ollama (macOS)
brew install ollama

# Or install on Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull Deepseek-R1:8B model
ollama pull deepseek-r1:8b
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd signaware-ai

# Install dependencies using uv
uv sync
```

### 2. Database Setup

Create your PostgreSQL database:

```sql
CREATE DATABASE signaware_db;
CREATE USER signaware_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE signaware_db TO signaware_user;
```

### 3. Environment Configuration

Copy the environment template:

```bash
cp env.template .env
```

Edit `.env` with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://signaware_user:your_password@localhost:5432/signaware_db

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b

# FastAPI Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### 4. Initialize Database

```bash
# Initialize database tables
uv run python scripts/init_db.py
```

### 5. Run the Application

```bash
# Start the application
uv run python run.py
```

The API will be available at:

- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### 👤 User Management

**POST** `/api/v1/users/` - Create a new user
**GET** `/api/v1/users/{user_id}` - Get user by ID
**GET** `/api/v1/users/email/{email}` - Get user by email

### 📋 Document Management

**POST** `/api/v1/documents/` - Create a new document
**GET** `/api/v1/documents/` - Get user documents
**GET** `/api/v1/documents/{document_id}` - Get specific document
**POST** `/api/v1/documents/{document_id}/analyze` - Analyze document
**GET** `/api/v1/documents/{document_id}/analysis` - Get analysis results

### 🔒 PII Masking

**POST** `/api/v1/pii/mask` - Mask PII in raw text
**POST** `/api/v1/pii/mask/document/{document_id}` - Mask PII in document
**GET** `/api/v1/pii/masked/{document_id}` - Get masked document content

### 💬 Chat Bot

**POST** `/api/v1/chat/stream` - Stream chat responses (SSE)
**POST** `/api/v1/chat/message` - Non-streaming chat
**GET** `/api/v1/chat/history/{session_id}` - Get chat history
**GET** `/api/v1/chat/sessions/{document_id}` - Get all chat sessions for document

## Usage Examples

### Complete Workflow Example

```python
import httpx
import asyncio
from uuid import uuid4

async def complete_workflow():
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # 1. Create a user
        user_response = await client.post(f"{base_url}/api/v1/users/", json={
            "email": f"user-{uuid4().hex[:8]}@example.com",
            "firstName": "Test",
            "lastName": "User",
            "password": "secure_password"
        })
        user = user_response.json()
        user_id = user['id']

        # 2. Create a document
        doc_response = await client.post(f"{base_url}/api/v1/documents/?user_id={user_id}", json={
            "title": "Privacy Policy",
            "content": "Your privacy policy content here...",
            "type": "privacy_policy"
        })
        document = doc_response.json()
        document_id = document['id']

        # 3. Analyze the document
        analysis_response = await client.post(
            f"{base_url}/api/v1/documents/{document_id}/analyze",
            json={"user_id": user_id}
        )
        analysis = analysis_response.json()
        print(f"Risk Score: {analysis['analysis']['risk_score']}/5")

        # 4. Chat about the document
        chat_response = await client.post(f"{base_url}/api/v1/chat/message", json={
            "message": "What are the main privacy concerns?",
            "session_id": f"session-{uuid4().hex[:8]}",
            "document_id": document_id,
            "user_id": user_id
        })
        chat = chat_response.json()
        print(f"AI Response: {chat['response']}")

# Run the example
asyncio.run(complete_workflow())
```

### Streaming Chat Example

```html
<!DOCTYPE html>
<html>
  <head>
    <title>SignAware AI Chat</title>
  </head>
  <body>
    <div id="chat-messages"></div>
    <script>
      const chatMessages = document.getElementById("chat-messages");

      // Replace with actual values
      const documentId = "your-document-uuid";
      const userId = "your-user-uuid";
      const sessionId = "session-123";

      fetch("http://localhost:8000/api/v1/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "Explain the key risks in this document",
          session_id: sessionId,
          document_id: documentId,
          user_id: userId,
        }),
      }).then((response) => {
        const reader = response.body.getReader();

        function readStream() {
          reader.read().then(({ done, value }) => {
            if (done) return;

            const chunk = new TextDecoder().decode(value);
            const lines = chunk.split("\n");

            lines.forEach((line) => {
              if (line.startsWith("data: ")) {
                const data = JSON.parse(line.slice(6));
                if (data.content) {
                  chatMessages.innerHTML += data.content;
                }
              }
            });

            readStream();
          });
        }

        readStream();
      });
    </script>
  </body>
</html>
```

## Testing

Run the comprehensive test suite:

```bash
# Test all endpoints
uv run python scripts/test_api.py
```

This will test:

- User creation and management
- Document upload and analysis
- PII masking (both text and document)
- Chat functionality with streaming
- Chat history and session management

## Development

### Install Development Dependencies

```bash
uv sync --group dev
```

### Code Formatting

```bash
uv run black app/
uv run isort app/
```

### Database Migrations

If you need to modify the database schema:

1. Update the models in `app/models.py`
2. Run the initialization script: `uv run python scripts/init_db.py`

## Project Structure

```
signaware-ai/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/             # API route handlers
│   │   ├── __init__.py
│   │   ├── users.py         # User management
│   │   ├── document_analysis.py # Document CRUD and analysis
│   │   ├── pii_masking.py   # PII masking endpoints
│   │   └── chat.py          # Chat and streaming
│   └── services/            # Business logic services
│       ├── __init__.py
│       ├── pii_masking.py   # PII masking logic
│       ├── document_analysis.py # Analysis logic
│       └── chat_service.py  # Chat and history management
├── scripts/
│   ├── setup.py            # Environment setup
│   ├── init_db.py          # Database initialization
│   └── test_api.py         # Comprehensive tests
├── pyproject.toml          # uv package configuration
├── env.template            # Environment variables template
├── run.py                  # Application runner
└── README.md
```

## Security Considerations

- User passwords should be hashed in production
- Implement proper authentication and authorization middleware
- Use HTTPS in production environments
- Regularly rotate API keys and secrets
- Implement rate limiting for API endpoints

## Performance Tips

- Use database connection pooling for high-traffic scenarios
- Implement caching for frequently accessed documents
- Consider using Redis for session management
- Monitor and optimize database queries
- Use async/await throughout for better performance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues:

- Open a GitHub issue
- Check the API documentation at `/docs`
- Review the test examples in `scripts/test_api.py`
