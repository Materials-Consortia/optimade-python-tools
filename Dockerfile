FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.23 /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/.venv \
    UV_PYTHON=python3.13 \
    PATH="/opt/.venv/bin:$PATH"

# Prevent writing .pyc files on the import of source modules
# and set unbuffered mode to ensure logging outputs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Copy repo contents
COPY pyproject.toml uv.lock LICENSE README.md .docker/run.sh ./
COPY optimade ./optimade
COPY providers/src/links/v1/providers.json ./optimade/server/data/
RUN apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/* \
    && uv sync --extra server --locked

# Setup server configuration
ARG CONFIG_FILE=optimade_config.json
COPY ${CONFIG_FILE} ./optimade_config.json
ENV OPTIMADE_CONFIG_FILE=/app/optimade_config.json

# Run app
EXPOSE 5000
ENTRYPOINT [ "/app/run.sh" ]
