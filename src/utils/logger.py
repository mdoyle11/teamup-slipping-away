# src/utils/logger.py
import logging
import sys


def setup_logger():
  logger = logging.getLogger("attendance_etl")
  logger.setLevel(logging.INFO)

  # Clear existing handlers to prevent duplicate lines
  if logger.hasHandlers():
    logger.handlers.clear()

  # Standard StreamHandler writes directly to stdout/stderr (ingested automatically by Cloud Run)
  handler = logging.StreamHandler(sys.stdout)
  formatter = logging.Formatter(
      "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
  )
  handler.setFormatter(formatter)
  logger.addHandler(handler)

  return logger


logger = setup_logger()