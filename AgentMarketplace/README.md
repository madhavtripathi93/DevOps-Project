# Agent Marketplace

A platform for discovering, building multi-agent AI automation pipelines.

## Setup

1. **Backend**:
   - `cd backend`
   - `pip install -r requirements.txt`
   - `uvicorn app.main:app --reload`

2. **Frontend**:
   - `cd frontend`
   - `npm install`
   - `npm run dev`

Alternatively, you can run the application using Docker Compose:
```bash
docker-compose up --build
```