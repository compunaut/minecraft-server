# Multi-platform Java 17 base; manifest digest verified for amd64 and arm64.
FROM itzg/minecraft-server:java17@sha256:044c379600c07cd58156e07511c68282501edeee8bc8212d0a6d8b6a3fb4185c
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-tomli && rm -rf /var/lib/apt/lists/*
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
