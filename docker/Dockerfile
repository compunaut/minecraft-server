# Multi-platform Java 17 base; manifest digest verified for amd64 and arm64.
FROM itzg/minecraft-server:2026.9.2-java17@sha256:0198cb9f0c7e7b1747645040e1245a6915c122662f3106f3b0979473a953ab61
USER root
COPY docker/tomli-requirements.txt /opt/tomli-requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir --no-deps --require-hashes -r /opt/tomli-requirements.txt
COPY pack.toml index.toml /opt/pack/
COPY mods/ /opt/pack/mods/
COPY config/ /opt/pack/config/
COPY scripts/pack.py /opt/pack-tool.py
COPY --chmod=755 docker/entrypoint.sh /opt/entrypoint.sh
RUN python3 /opt/pack-tool.py --root /opt/pack validate
ENV TYPE=FORGE MEMORY=16G ENABLE_RCON=false
EXPOSE 25565/tcp
VOLUME ["/data"]
STOPSIGNAL SIGTERM
ENTRYPOINT ["/opt/entrypoint.sh"]
