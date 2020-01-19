FROM python:3.7

WORKDIR /app

# copy repo contents
COPY setup.py README.md ./
COPY optimade ./optimade
RUN pip install -e .[server]

EXPOSE 80

COPY run.sh ./

CMD ["/app/run.sh", "$MAIN"]
