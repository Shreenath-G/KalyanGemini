"""Application configuration management"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    # Google Cloud
    google_cloud_project: str
    google_cloud_region: str = "us-central1"
    google_application_credentials: Optional[str] = None
    
    # Vertex AI
    vertex_ai_location: str = "us-central1"
    vertex_ai_model: str = "gemini-pro"
    
    # Firestore
    firestore_database: str = "(default)"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_key_header: str = "X-API-Key"
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    
    # Agent Configuration
    adk_config_path: str = "config/adk_config.yaml"
    agent_timeout_seconds: int = 30
    bid_execution_timeout_ms: int = 100
    
    # Performance Monitoring
    performance_check_interval_minutes: int = 15
    
    # Budget Configuration
    test_budget_percentage: float = 0.20
    min_campaign_budget: float = 100.0
    max_campaign_budget: float = 100000.0
    
    # Optimization Thresholds
    min_roas_threshold: float = 1.0
    high_roas_threshold: float = 3.0
    pause_roas_threshold: float = 0.5
    min_clicks_for_decision: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
