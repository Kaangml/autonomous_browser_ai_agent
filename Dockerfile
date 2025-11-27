# Multi-stage Dockerfile for Autonomous Browser AI Agent
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install Playwright dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    # Fonts
    fonts-liberation \
    fonts-noto-color-emoji \
    # Utilities
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=builder /root/.local/bin/uv /usr/local/bin/uv

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Copy source code
COPY src/ ./src/
COPY pyproject.toml ./

# Install Playwright browsers
RUN playwright install chromium

# Create non-root user for security
RUN useradd -m -u 1000 agent
RUN chown -R agent:agent /app
USER agent

# Environment variables (override at runtime)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BROWSER_HEADLESS=true

# Default command
ENTRYPOINT ["python", "-m", "src"]
CMD ["--help"]

# Example usage:
# docker build -t browser-agent .
# docker run -e GEMINI_API_KEY=xxx browser-agent --url "https://example.com" --task "extract title"
