"""
Configuration module for Dreamwell Assessment

This module contains all environment variables and configuration settings.
Shared between backend_main.py and mcp_server.py.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
EMAIL_FIXTURES_PATH = DATA_DIR / "email_fixtures.json"
YOUTUBE_PROFILES_PATH = DATA_DIR / "youtube_profiles.json"
BRAND_PROFILES_PATH = DATA_DIR / "brand_profiles.json"

# Server Configuration
FASTAPI_HOST = "0.0.0.0"
FASTAPI_PORT = 8000

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# YouTube API Configuration
YOUTUBE_CACHE_DURATION_HOURS = 24
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Agent Configuration
MAX_AGENT_ITERATIONS = 5
AGENT_TIMEOUT_SECONDS = 45
DEFAULT_LLM_MODEL = "gpt-4o"

# Logging Configuration
LOG_FILE = "server.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
