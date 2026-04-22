# A.R.I.A. Studio Frontend

This is the Vite React frontend for A.R.I.A. Studio.

Run the Python API:

```powershell
uvicorn api.main:app --reload --port 8000
```

Run the frontend after Node.js is installed:

```powershell
cd frontend
npm install
npm run dev
```

Vite proxies `/api` requests to `http://127.0.0.1:8000`.
