FROM python:3.7

WORKDIR /app

# copy repo contents
COPY / ./
RUN pip install -e .[server]

ARG PORT=5000
EXPOSE ${PORT}

COPY src/docker/run.sh ./

CMD ["/app/run.sh"]
