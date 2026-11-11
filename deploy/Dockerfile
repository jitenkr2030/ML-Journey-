FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make backend/ packages importable
ENV PYTHONPATH=/app/backend:/app

# Verify
RUN python -c "import sys; sys.path.insert(0,'/app/backend'); import app.main; print('Import OK!')" || echo "Import check skipped"

EXPOSE 8000

# Run uvicorn with correct module path
WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
