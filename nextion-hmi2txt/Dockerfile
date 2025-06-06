FROM alpine/curl:latest

RUN mkdir -p /usr/src/app

RUN curl https://raw.githubusercontent.com/sztupy/Nextion2Text/refs/heads/master/Nextion2Text.py > /usr/src/app/Nextion2Text.py


FROM python:3

WORKDIR /data

RUN mkdir -p data

COPY --from=0 /usr/src/app/Nextion2Text.py /data/Nextion2Text.py

ENTRYPOINT [ "python", "/data/Nextion2Text.py" ]