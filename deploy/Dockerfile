# ReconcileAI - Production Dockerfile
# Updated: 2026-11-11 (fixed: copy ALL files)

FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL project files (ensures nothing is missed!)
COPY . .

# Make sure key files exist
RUN echo "=== Verifying files ===" && \
    ls -la index.html tools.html faq.html compare.html && \
    ls -la best-reconciliation-software-india.html extensions.html && \
    ls -la footer.html sitemap.xml robots.txt favicon.svg && \
    ls -la festival-config.js festival-themes.css festival-engine.js && \
    echo "=== All files present ==="

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
