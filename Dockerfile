FROM python:3.11-slim

# Prevent writing .pyc files on the import of source modules
# and set unbuffered mode to ensure logging outputs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Copy repo contents
COPY pyproject.toml requirements.txt requirements-server.txt LICENSE README.md .docker/run.sh ./
COPY optimade ./optimade
COPY providers/src/links/v1/providers.json ./optimade/server/data/
RUN apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -U pip setuptools wheel flit \
    && pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt -r requirements-server.txt \
    && pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org .[server]

# Setup server configuration
ARG CONFIG_FILE=optimade_config.json
COPY ${CONFIG_FILE} ./optimade_config.json
ENV OPTIMADE_CONFIG_FILE=/app/optimade_config.json

# Run app
EXPOSE 5000
ENTRYPOINT [ "/app/run.sh" ]
