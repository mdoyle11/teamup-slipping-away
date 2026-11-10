# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
  """Centralized configuration and secret validation."""

  # API & Sheet Identifiers
  M2M_TOKEN = os.getenv("M2M_TOKEN").strip()

  # Email / Notification Credentials
  APP_PASSWORD = os.getenv("APP_PASSWORD")
  SENDER_EMAIL = os.getenv("SENDER_EMAIL")
  RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

  @classmethod
  def ensure_token(cls) -> str:
    """Ensures TeamUp M2M token is present."""
    if not cls.M2M_TOKEN:
      raise ValueError("Missing M2M Token.")
    return cls.M2M_TOKEN