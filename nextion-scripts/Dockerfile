FROM sztupy/nextion-editor:1.68.2

RUN apt-get update \
  && DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
  psmisc curl \
  && rm -rf /var/lib/apt/lists/* && mkdir -p /app

RUN curl https://raw.githubusercontent.com/edwardtfn/Nextion2Text/61da2a1925b5e08b9ca8fee414e76fca42a69211/Nextion2Text.py > /app/Nextion2Text.py

COPY . /app

RUN echo 'wineuser ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

WORKDIR "/app"
