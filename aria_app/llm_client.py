from __future__ import annotations
from openai import OpenAI
from storage import load_vault_settings

def get_llm_client() -> OpenAI:
    settings = load_vault_settings()
    base_url = settings.get("MODEL_ENDPOINT") or settings.get("model_endpoint") or "http://127.0.0.1:3010/v1"
    return OpenAI(base_url=base_url, api_key="lm-studio")

def get_model_name() -> str:
    settings = load_vault_settings()
    return settings.get("MODEL_NAME") or settings.get("model_name") or "google/gemma-4-e2b"
