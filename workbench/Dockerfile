ARG BASE_IMAGE=sztupy/nextion-scripts@sha256:246a69a268419e333b3654984f9640a43f9db256f2356e09030d695ac5ef9a5e
FROM ${BASE_IMAGE} AS dependencies
USER root
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    x11vnc novnc websockify openbox xdotool xclip fonts-nanum tini \
    && rm -rf /var/lib/apt/lists/*
ARG EDITOR_VERSION=1.68.2
ARG EDITOR_SHA256=1a00e05e86bc66f977ffaec7da3b9c8387233828021a07560b14e2efe2b8ff2d
COPY downloads/nextion-1.68.2.zip /tmp/editor.zip
RUN echo "${EDITOR_SHA256}  /tmp/editor.zip" | sha256sum -c - \
    && rm -rf /home/wineuser/.wine/drive_c/data/nextion \
    && mkdir -p /home/wineuser/.wine/drive_c/data/nextion \
    && unzip -q /tmp/editor.zip -d /home/wineuser/.wine/drive_c/data/nextion \
    && test -f '/home/wineuser/.wine/drive_c/data/nextion/Nextion Editor.exe' \
    && chown -R wineuser:wineuser /home/wineuser/.wine/drive_c/data/nextion \
    && rm /tmp/editor.zip

FROM dependencies AS prepared
RUN mkdir -p /workspace /input /opt/web \
    && cp -a /usr/share/novnc/. /opt/web/

FROM prepared AS full
ENV NEXTION_EDITOR_VERSION=1.68.2 WINEARCH=win32 WINEPREFIX=/home/wineuser/.wine DISPLAY=:95 WINEDEBUG=-all PYTHONUNBUFFERED=1
ENV WINEDLLOVERRIDES=""
COPY runtime.py metrics.py compile.ahk bootstrap.ahk windows.ahk web_proxy.py /opt/workbench/
COPY web/ /opt/web/
WORKDIR /workspace
EXPOSE 6080
ENTRYPOINT ["/usr/bin/tini", "--", "python3", "/opt/workbench/runtime.py"]
CMD ["editor"]
HEALTHCHECK --interval=5s --timeout=3s --start-period=60s CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:6080/api/status', timeout=2)"

FROM prepared AS pruned
# This runtime has a preinstalled, strictly win32 prefix. Keep the 64-bit
# Linux wineserver, all 32-bit Wine libraries, .NET, fonts, and diagnostics.
# Firefox, Vim, Wine64, and Mono installer archives belong to the full image.
RUN rm -rf /home/wineuser/.wine/drive_c/data/MacroCreatorPortable \
    /home/wineuser/.wine/drive_c/data/*.zip /home/wineuser/.wine/drive_c/data/*.exe \
    /home/wineuser/.wine/drive_c/data/ahk/Compiler /home/wineuser/.cache \
    /root/.cache /var/cache/apt/archives/* /usr/share/doc/* /usr/share/man/* \
    /opt/wine-stable/lib64 /opt/wine-stable/bin/wine64 /opt/wine-stable/bin/wine64-preloader \
    /usr/bin/wine64 /usr/bin/wine64-preloader /usr/lib/firefox /usr/bin/firefox \
    /usr/share/vim /usr/share/wine/mono /usr/share/wine/gecko

FROM scratch AS runtime-base
# Flatten only dependencies: editing Python/AHK/HTML no longer rewrites this
# multi-gigabyte layer. The small application layers remain independently cached.
COPY --from=pruned / /

FROM runtime-base AS slim
# The Editor's online update view needs Gecko even though offline TFT builds
# do not. Keep this small optional cache separate from the flattened core.
COPY --from=dependencies /usr/share/wine/gecko /usr/share/wine/gecko
ENV NEXTION_EDITOR_VERSION=1.68.2 WINEARCH=win32 WINEPREFIX=/home/wineuser/.wine DISPLAY=:95 WINEDEBUG=-all PYTHONUNBUFFERED=1
ENV WINEDLLOVERRIDES=""
COPY runtime.py metrics.py compile.ahk bootstrap.ahk windows.ahk web_proxy.py /opt/workbench/
COPY web/ /opt/web/
WORKDIR /workspace
EXPOSE 6080
ENTRYPOINT ["/usr/bin/tini", "--", "python3", "/opt/workbench/runtime.py"]
CMD ["editor"]
HEALTHCHECK --interval=5s --timeout=3s --start-period=60s CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:6080/api/status', timeout=2)"
