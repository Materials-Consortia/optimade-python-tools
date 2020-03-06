FROM python:3.7

WORKDIR /app

# copy repo contents
COPY src/setup.py src/README.md ./
COPY src/optimade ./src/optimade
RUN pip install -e .[server]

ARG PORT=5000
EXPOSE ${PORT}

COPY src/docker/run.sh ./

CMD ["/app/run.sh"]
