# 🐞 Intelligent Bug Triage System – Backend

THe frontend repo for this back - https://github.com/RohithRamesh28/Intelligent-Bug-Triage-System-frontend.git


This is the backend of the **Intelligent Bug Triage System**, designed to analyze uploaded projects (single files or zipped codebases), detect bugs and risky code patterns using static analysis and GPT-4o, and store results in MongoDB.

## 🚀 Features

- 🔍 Project-wide bug detection using GPT-4o
- 📁 Upload support for `.py`, `.js`, `.ts`, `.zip`,etc
- 📦 Intelligent grouping & chunking of files for contextual analysis
- 📡 Real-time WebSocket progress updates during processing
- ✅ JWT-based authentication with role support
- 🧠 Optimization hints (non-generative suggestions)
- 💾 Results stored in MongoDB, retrievable by upload
- 📊 Integrated with frontend dashboard

---

## 📂 Project Structure

backend/

├── main.py # FastAPI app entrypoint

├── routes/ # All API routes (auth, upload, bug analysis)

│ └── ...

├── services/ # GPT analysis, file chunking, etc.

├── utils/ # Auth utilities, token handling, etc.

├── db/ # MongoDB connection setup

├── websocket/ # WebSocket manager for real-time updates

└── schemas/ # Pydantic models

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/intelligent-bug-triage-system.git
cd intelligent-bug-triage-system/backend
2. Create & Activate Virtual Environment

python -m venv bug_triage_env
source bug_triage_env/bin/activate  # or .\bug_triage_env\Scripts\activate on Windows
3. Install Dependencies

pip install -r requirements.txt
Make sure MongoDB is running locally or update the connection URI in .env.

📄 Environment Variables
Create a .env file with the following variables:


MONGODB_URI=mongodb://localhost:27017
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
🧪 Running the Server

uvicorn main:app --host 0.0.0.0 --port 8080 --reload
The API will be available at: http://localhost:8080

🔐 Auth Endpoints
POST /register – Create a new user

POST /login – Get JWT token

Requires token in Authorization: Bearer <token> header for protected routes

📤 Upload & Analysis
POST /upload/ – Upload files or zipped project

GET /ws/progress/{upload_id} – WebSocket for real-time progress

GET /file_bugs/{upload_id} – Get bug and optimization results

GET /project/my-uploads – Fetch uploads by the authenticated user

🧠 GPT Analysis Flow
Files are grouped contextually (e.g., /routes, /utils)

Static checks (e.g., Pylint, ESLint) are applied

GPT-4o processes grouped files for:

Bugs (e.g., unhandled cases, insecure code)

Optimization hints (e.g., loops, redundancy)

Output is saved in MongoDB with:

file_path, line, description, priority, author, etc.

🧾 MongoDB Schema (Simplified)

{
  "upload_id": "abc123",
  "zip_name": "project_23.zip",
  "file_path": "src/services/logic.py",
  "bugs": [
    {
      "line": 45,
      "description": "Unhandled case in switch statement",
      "priority": "High",
      "author": "Uploaded by user"
    }
  ]
}


 GPT-4o for context-aware analysis

📦 Dependencies
Major packages used:

fastapi

motor (async MongoDB)

websockets

httpx / aiohttp

passlib, bcrypt (for authentication)

openai (GPT-4o integration)

python-dotenv

✨ Future Plans
GitHub sync & Git blame integration

Admin roles and reviewer assignment

CSV/PDF export of bug reports

Jira/Slack integration

