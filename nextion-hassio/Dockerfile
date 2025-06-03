FROM sztupy/nextion-scripts

RUN (apt-get update || true) \
    && DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
        jq \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

CMD /app/run.sh