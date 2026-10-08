# Epic Fight server and client pack

A Minecraft Java Edition **1.20.1** modpack featuring **Epic Fight 20.14.17**, running on **Forge 47.4.10**. Includes a Docker server image and a matching CurseForge client pack.

## Downloads

- **Server:** `ghcr.io/compunaut/minecraft-server:latest`
- **Client:** versioned ZIPs in [client-packs/](client-packs/), also available from [Releases](https://github.com/compunaut/minecraft-server/releases).

Client ZIPs are added to the download folder by the release workflow when a version tag is published. Before the first release, the ZIP is available as the `client-pack` artifact on a successful [Actions build](https://github.com/compunaut/minecraft-server/actions).

## Run the server with Docker

Install Docker Engine or Docker Desktop. Read the [Minecraft EULA](https://aka.ms/MinecraftEULA) before accepting it with `EULA=TRUE`.

```sh
docker pull ghcr.io/compunaut/minecraft-server:latest

docker run -d --name epic-fight \
  --restart unless-stopped --stop-timeout 120 \
  -p 25565:25565 \
  -e EULA=TRUE -e MEMORY=16G \
  -v "$(pwd)/minecraft-data:/data" \
  ghcr.io/compunaut/minecraft-server:latest
```

The server uses a maximum Java heap of **16 GB**. Change `MEMORY` to suit your machine and leave memory for the operating system. The image includes Java 17 and supports AMD64 and ARM64 hosts; use a 64-bit operating system on Raspberry Pi.

Worlds, settings, and player data persist in `minecraft-data/`. The first startup downloads Forge and the pinned server mods, so allow time for installation.

### Docker Compose

From a checkout of this repository:

```sh
cp .env.example .env
```

Set `EULA=TRUE` in `.env` and choose an available `IMAGE_TAG` (`latest` or a release such as `v1.0.0`). Adjust `MEMORY` if needed, then start:

```sh
docker compose pull
docker compose up -d
docker compose logs -f
```

## Install the client on Windows

Players need Minecraft Java Edition and the [CurseForge app](https://www.curseforge.com/download/app).

1. Download the ZIP matching the server's pack version from [client-packs/](client-packs/). Open the ZIP's GitHub file page and select **Download raw file**, or download it from Releases.
2. In CurseForge, select **Minecraft → Import → Import Profile .zip** and choose the downloaded ZIP. Do not extract it first.
3. Wait for the mods to install, then launch the profile.
4. In Minecraft, select **Multiplayer → Add Server** and enter the server address.

Players do not need Docker, Git, or developer tools. If downloading an Actions artifact, extract its outer archive once and import the `epic-fight-pack-vX.Y.Z.zip` inside. See [CurseForge's import guide](https://support.curseforge.com/support/solutions/articles/9000197912).

## Manage the server

```sh
docker logs -f epic-fight     # View startup and server logs
docker stop epic-fight        # Save and stop the server
docker start epic-fight       # Start it again
```

For Compose deployments, use `docker compose logs -f`, `docker compose down`, and `docker compose up -d`.

Stop the server before backing up the entire `minecraft-data/` directory. Before upgrading, make a backup and choose the matching release image and client ZIP. For Compose, change `IMAGE_TAG`, then run `docker compose pull` and `docker compose up -d`. Restore the pre-upgrade backup when rolling back.

## Distribution and reproducibility

[Packwiz](https://packwiz.infra.link/) metadata pins the Minecraft and Forge versions, exact mod file IDs, checksums, and client/server sides. The server image and client ZIP are built from the same source revision for each release. Use a versioned image tag or digest and the matching client ZIP to reproduce a release.

The client ZIP contains CurseForge file references and shared configuration; CurseForge downloads the specified mods during import. The server downloads its pinned mods at startup and verifies their checksums. Mod JARs, worlds, and player data are not bundled in the repository or image. Embeddium is included on clients only.

Downloads require network access and availability of the upstream files. Published ZIP versions are retained in `client-packs/` with SHA-256 checksums and are never overwritten.
