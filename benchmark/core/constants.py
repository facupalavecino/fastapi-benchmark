import os
from pathlib import Path

PROJECT_NAME = "FastAPI Benchmark"

CONSTANTS_DIR = os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = (Path(CONSTANTS_DIR) / "..").resolve()
"""Root directory"""

LOGS_DIR = (ROOT_DIR / ".." / "logs").resolve()
"""Directory where logs are saved"""
