"""
Database and application configuration.
"""

import os
from typing import Optional


class Settings:
    """Application settings."""

    def __init__(self):
        # Database
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/ondo",
        )

        # Application
        self.app_name: str = "Ondo"
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"

        # AI Assist (optional feature)
        self.ai_assist_enabled: bool = os.getenv(
            "AI_ASSIST_ENABLED", "false"
        ).lower() == "true"


settings = Settings()

