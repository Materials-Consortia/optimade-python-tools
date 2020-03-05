FROM python:3.7

RUN pip install -U pip setuptools wheel \
    && git clone https://github.com/Materials-Consortia/optimade-python-tools \
    && pip install -U -e ./optimade-python-tools

RUN echo $(ip route | awk '{print $3}') > /docker_host_ip

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]
