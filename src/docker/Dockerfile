FROM python:3.7

WORKDIR /app

# copy repo contents
COPY setup.py README.md ./
COPY src/optimade ./src/optimade
RUN pip install -e .[server]

ARG PORT=5000
EXPOSE ${PORT}

COPY .docker/run.sh ./

CMD ["/app/run.sh"]
