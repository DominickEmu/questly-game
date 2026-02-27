# Questly 🗡️

A gamified to-do list app where tasks are **quests** that earn you XP, coins, and gems. Built with React + FastAPI.

---

## Prerequisites

Make sure you have the following installed before getting started:

- [Node.js](https://nodejs.org/) (v18 or higher)
- [Python](https://www.python.org/downloads/) (v3.10 or higher)
- [Git](https://git-scm.com/)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/DominickEmu/questly-game.git
cd questly-game
```

### 2. Set up the backend

```bash
cd backend
pip install -r requirements.txt
```

### 3. Set up the frontend

```bash
cd ../frontend
npm install
```

---

## Running the App

You need **two terminals** running at the same time.

**Terminal 1 — Backend (port 8000)**
```bash
cd backend
python -m uvicorn main:app --reload
```

**Terminal 2 — Frontend (port 5173)**
```bash
cd frontend
npm run dev
```

Then open your browser and go to: **http://localhost:5173**

The frontend automatically proxies `/api` requests to the backend, so no extra configuration is needed.

---

## First Run

On first launch, the backend will:
- Automatically create the SQLite database (`backend/questly.db`)
- Seed default shop items and a starter profile

No manual database setup required.

---

## Troubleshooting

**Port 8000 already in use (Windows)**
```powershell
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force
```

**Reset the database**

Delete `backend/questly.db` and restart the backend — it will recreate and re-seed automatically.

---

## Tech Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Frontend | React 18, Vite, React Router, CSS Modules |
| Backend  | Python, FastAPI, SQLAlchemy         |
| Database | SQLite                              |
