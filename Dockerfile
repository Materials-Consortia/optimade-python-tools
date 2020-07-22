FROM python:3.7

WORKDIR /app

# copy repo contents
COPY setup.py README.md ./
COPY optimade ./optimade
COPY providers/src/links/v1/providers.json ./optimade/server/data/
RUN pip install -e .[server]

ARG PORT=5000
EXPOSE ${PORT}

COPY .docker/run.sh ./

ARG CONFIG_FILE=optimade_config.json
COPY ${CONFIG_FILE} ./config.json
ENV OPTIMADE_CONFIG_FILE /app/config.json

CMD ["/app/run.sh"]
