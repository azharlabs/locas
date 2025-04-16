from dataclasses import dataclass
import httpx
import os
from typing import Optional

@dataclass
class ServiceConfig:
    """Configuration for the Maps and related services."""
    api_key: str
    http_client: httpx.AsyncClient
    default_radius: int = 1500  # Default radius in meters
    default_language: str = "en"
    max_result_retries: int = 2  # Maximum number of retries for validation

@dataclass
class AppConfig:
    """Application configuration with all settings."""
    openai_api_key: str
    maps_api_key: str
    serper_api_key: str
    default_radius: int = 1500
    default_language: str = "en"
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY", ""),
            serper_api_key=os.getenv("SERPER_API_KEY", ""),
            default_radius=int(os.getenv("DEFAULT_RADIUS", "1500")),
            default_language=os.getenv("DEFAULT_LANGUAGE", "en")
        )
    
    def create_service_config(self, http_client: httpx.AsyncClient) -> ServiceConfig:
        """Create a service configuration from app configuration."""
        return ServiceConfig(
            api_key=self.maps_api_key,
            http_client=http_client,
            default_radius=self.default_radius,
            default_language=self.default_language
        )