"""Configuration management using Pydantic Settings."""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required
    anthropic_api_key: str = Field(..., description="Anthropic API key")

    # Environment
    environment: Literal["development", "production"] = Field(
        default="development", description="Environment mode"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )

    # Server Configuration
    fastapi_host: str = Field(default="0.0.0.0", description="FastAPI host")
    fastapi_port: int = Field(default=8000, description="FastAPI port")

    # RAG Configuration
    top_k_results: int = Field(default=3, description="Number of documents to retrieve")
    similarity_threshold: float = Field(
        default=0.5, description="Similarity threshold for exact match (0-1)"
    )
    collection_name: str = Field(
        default="thoughtful_ai_qa", description="ChromaDB collection name"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="HuggingFace embedding model"
    )
    chroma_db_path: str = Field(default="./chroma_db", description="ChromaDB storage path")

    # Claude Configuration
    claude_model: str = Field(
        default="claude-sonnet-4-20250514", description="Claude model identifier"
    )
    max_tokens: int = Field(default=1000, description="Max tokens for Claude responses")
    temperature: float = Field(default=0.3, description="Claude temperature")

    # Observability
    enable_tracing: bool = Field(default=True, description="Enable OpenTelemetry tracing")
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")

    # Data paths
    qa_dataset_path: str = Field(
        default="./data/qa_dataset.json", description="Path to Q&A dataset"
    )


# Global settings instance
settings = Settings()
