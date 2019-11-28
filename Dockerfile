FROM python:3.7

WORKDIR /app

# copy repo contents
COPY setup.py README.md ./
COPY optimade ./optimade
RUN pip install -e .[mongo]
RUN pip install uvicorn

EXPOSE 80

ENV MAIN main

COPY run.sh ./

CMD ["/app/run.sh", "$MAIN"]
