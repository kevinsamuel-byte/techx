# Personal Career Navigator

Full-stack project with separate folders as requested:

- `backend/` -> FastAPI backend
- `front end/` -> Next.js frontend

## What is implemented

- Login/onboarding page with:
  - LinkedIn connect
  - GitHub connect
  - Resume upload (`pdf`, `docx`, `txt`)
  - AI resume builder redirect
- Resume ingestion with NLP-lite extraction into persistent user state:
  - skills
  - education/experience/projects/achievements
  - resume summary/raw text
- Dashboard with interactive roadmap orbit:
  - goal at center
  - education, softskills, certification nodes around goal
  - mentorship, mock test, mock interview support nodes
  - glowing goal with stars when core modules hit 100%
- Separate pages:
  - Education roadmap mindmap
  - Softskills roadmap mindmap
  - Certification programs (Coursera/Udemy recommendations)
- AGENT GURU floating chat:
  - explain reasoning
  - change goal
  - remove modules
  - mark module tasks
  - update or create resume
- Persistent database-backed state (SQLite by default)
- API test file included in `backend/tests/test_api.py`

## Project structure

```text
backend/
  __init__.py
  main.py
  models.py
  schemas.py
  db.py
  config.py
  services/
  tests/
  requirements.txt

front end/
  package.json
  next.config.mjs
  tsconfig.json
  src/
```

## Run backend

```bash
cd /Users/lijopaul/Downloads/TECHX
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

## Run frontend

```bash
cd "/Users/lijopaul/Downloads/TECHX/front end"
npm install
npm run dev
```

Set API base if needed:

```bash
export NEXT_PUBLIC_API_BASE="http://localhost:8000/api"
```

## Test backend

```bash
cd /Users/lijopaul/Downloads/TECHX
pytest backend/tests -q
```
