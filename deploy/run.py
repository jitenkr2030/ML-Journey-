"""
Root-level launcher for Docker/Deplexo.
Ensures 'app' module is importable regardless of working directory.
"""
import sys
import os

# Add backend/ to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
