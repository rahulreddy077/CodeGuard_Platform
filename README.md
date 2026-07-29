# CodeGuard

CodeGuard is a comprehensive code security and analysis suite featuring code quality metrics, AST-based inspection, plagiarism detection, and AI generation analysis.

## Project Structure

- `backend/` - FastAPI backend application (API, database, auth, models, services)
- `frontend/` - Streamlit multi-page dashboard application
- `modules/` - Core analysis engines (plagiarism, AI detection, quality, AST parser)
- `datasets/` - Directory for training or analysis code snippets
- `models/` - Location for model weights and tokenizer configurations
- `reports/` - Output directory for generated code audit reports
- `tests/` - pytest test suite
- `docs/` - System architecture and user guides

## Getting Started

### 1. Installation

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Running the Backend

Start the FastAPI application:

```bash
uvicorn backend.main:app --reload
```

The interactive API docs will be available at `http://127.0.0.1:8000/docs`.

### 3. Running the Frontend

Start the Streamlit dashboard:

```bash
streamlit run frontend/app.py
```
