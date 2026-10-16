FROM sztupy/nextion-scripts:0.2.0

RUN apt-get update && apt-get install python3 python3-pip python3-yaml -y
COPY . /app

CMD /app/run.sh
