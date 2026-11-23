import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings,SettingsConfigDict


#1.Find the project root folder
BASE_DIR=Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
  PROJECT_NAME:str = 'AI Code Review & Repository Assistant'
  VERSION: str = "1.0.0"
  API_V1_STR: str = "/api/v1"

  # DATABASE settings
  DATABASE_URL:str =Field(
    default=None
  )

  ## LLM settings
  GEMINI_API_KEY:Optional[str]=Field(default=None)
  ## Webhook settings
  GITHUB_WEBHOOK_SECRET:Optional[str]=Field(default=None)

  # Tell pydantic to read from the .env
  model_config=SettingsConfigDict(
    env_file=str(BASE_DIR/".env"),
    extra="ignore" # Ignore any extra keys in .env that aren't defined here
  )


settings=Settings()
