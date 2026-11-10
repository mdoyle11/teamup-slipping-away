FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy dependency definition and lockfile if present
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv sync
RUN uv sync --frozen --no-cache

# Copy application source code
COPY src/ ./src

CMD ["uv", "run", "src/main.py"]