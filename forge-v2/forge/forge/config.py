from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core LLM ---
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"

    # --- Storage ---
    database_path: str = "data/projects.db"
    workspace_root: str = "generated_projects"
    rag_corpus_path: str = "data/rag_corpus.json"

    # --- Limits ---
    allow_host_test_execution: bool = False
    test_timeout_seconds: int = 45
    max_generated_files: int = 12
    max_file_chars: int = 30000

    # --- Feature: Auto-repair loop ---
    enable_repair_loop: bool = True
    max_repair_iterations: int = 2
    repair_score_threshold: int = 80

    # --- Feature: Token / cost telemetry ---
    # Groq gpt-oss-20b pricing (USD per million tokens) — adjust to your plan.
    input_cost_per_mtok: float = 0.10
    output_cost_per_mtok: float = 0.15

    # --- Feature: RAG over past projects ---
    enable_rag: bool = True
    rag_top_k: int = 3

    # --- Feature: GitHub export ---
    enable_github_export: bool = False
    github_token: str = ""
    github_default_visibility: str = "private"

    # --- Feature: Docker sandboxed test execution ---
    enable_docker_sandbox: bool = False
    docker_image: str = "python:3.12-slim"
    docker_timeout_seconds: int = 120
    docker_network_disabled: bool = True
    docker_memory_limit: str = "512m"
    docker_cpus: str = "1.0"

    @property
    def workspace_directory(self) -> Path:
        p = Path(self.workspace_root)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
