"""
Configuration settings using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Supabase
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_KEY: str = "your-anon-key-here"
    SUPABASE_SERVICE_KEY: str = "your-service-role-key-here"  # For admin operations
    
    # Database (Supabase Postgres)
    DATABASE_URL: str = "postgresql://postgres:Poi09q13??!!@db.your-project.supabase.co:5432/postgres"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # CORS - will be split on comma
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
