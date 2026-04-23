# TriggerPoints AI

Monorepo containing frontend and backend for the TriggerPoints AI service.

## Structure

```
├── frontend/    # React + Vite frontend
├── backend/     # Python FastAPI backend
└── README.md
```

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```
