# Epic Fight server and client pack

A Minecraft Java Edition **1.20.1** modpack featuring **Epic Fight 20.14.17**, running on **Forge 47.4.10**. Includes a Docker server image and a matching CurseForge client pack.

## Downloads

- **Server:** `ghcr.io/compunaut/minecraft-server:latest`
- **Client:** versioned ZIPs in [client-packs/](client-packs/), also available from [Releases](https://github.com/compunaut/minecraft-server/releases).

Client ZIPs are added to the download folder automatically when a new pack version is released. Before the first release, the ZIP is available as the `client-pack` artifact on a successful [Actions build](https://github.com/compunaut/minecraft-server/actions).

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

## Install the client on macOS

Players need Minecraft Java Edition and the [CurseForge app for macOS](https://www.curseforge.com/download/app). CurseForge supports macOS 12 or newer; see its [platform requirements](https://support.curseforge.com/support/solutions/articles/9000193488-getting-started).

1. Install CurseForge and select Minecraft.
2. Download the matching client ZIP from [client-packs/](client-packs/) or Releases. If Safari extracts it automatically, download it again with automatic extraction disabled; import the ZIP itself.
3. Select **Import → Import Profile .zip**, choose the ZIP, and wait for installation.
4. Launch the profile, sign into your Minecraft account, then select **Multiplayer → Add Server** and enter the server address.

## Install the client on Linux

On Ubuntu, install the [CurseForge Linux app](https://www.curseforge.com/download/app) and follow the Windows import steps above. CurseForge's official Linux support covers Ubuntu distributions.

For other distributions, use [Prism Launcher](https://prismlauncher.org/download/linux/), available for x86-64 and ARM64:

1. Install Prism using its download page or your distribution's software center, then add the Microsoft account that owns Minecraft Java Edition.
2. Download the matching client ZIP from [client-packs/](client-packs/) or Releases.
3. Select **Add Instance → Import**, choose the ZIP, and complete installation. If Prism asks you to download a restricted CurseForge file in your browser, follow its prompts for that exact file.
4. Use **Java 17** for this instance. Enable automatic Java detection/download where available, or install Java 17 for your CPU architecture and select it in the instance settings.
5. Launch the instance, select **Multiplayer → Add Server**, and enter the server address.

See Prism's [ZIP import guide](https://prismlauncher.org/wiki/getting-started/download-modpacks/) and [Java setup guide](https://prismlauncher.org/wiki/getting-started/installing-java/).

## Raspberry Pi

### Run the server

1. Use a 64-bit Raspberry Pi OS or Ubuntu installation and install [Docker Engine](https://docs.docker.com/engine/install/debian/) with the Compose plugin. For Raspberry Pi OS, use the instructions for its corresponding Debian release; for Ubuntu, use [Docker's Ubuntu installation guide](https://docs.docker.com/engine/install/ubuntu/).
2. Follow the Docker or Compose server instructions above. Docker selects the ARM64 image automatically.
3. Adjust memory to your board: on an 8 GB Pi, start with `MEMORY=4G` instead of `16G`, leaving room for the OS and Java overhead.
4. Wait for installation to finish in the server logs, then connect from a separate computer using the Pi's network address and the matching client pack.

An ARM64 image is provided, but this modpack's performance on Raspberry Pi has not been verified. Choose memory and view distance conservatively and test with your expected player count.

### Install the client

Use a 64-bit desktop OS, the ARM64 version of [Prism Launcher](https://prismlauncher.org/download/linux/), and ARM64 Java 17. Follow the Linux ZIP import steps above. Prism also lists a Pi-Apps installation option.

Launcher availability does not guarantee that this Epic Fight pack runs well on a Pi; its graphics compatibility and gameplay performance on that hardware have not been verified. Minecraft Pi Edition and Bedrock Edition cannot join this Java/Forge server.

## Manage the server

```sh
docker logs -f epic-fight     # View startup and server logs
docker stop epic-fight        # Save and stop the server
docker start epic-fight       # Start it again
```

For Compose deployments, use `docker compose logs -f`, `docker compose down`, and `docker compose up -d`.

Stop the server before backing up the entire `minecraft-data/` directory. Before upgrading, make a backup and choose the matching release image and client ZIP. For Compose, change `IMAGE_TAG`, then run `docker compose pull` and `docker compose up -d`. Restore the pre-upgrade backup when rolling back.

## Releases

Every successful build on `main` updates the `latest` server image. If the version in `pack.toml` has no published version tag yet, that build also publishes `vX.Y.Z`: a matching GHCR image, a GitHub Release, and the client ZIP/checksum in `client-packs/`.

To release an update, increment the pack version in a reviewed PR and merge it into `main`. Validation and the AMD64/ARM64 image build must pass before the workflow creates the tag and release. Documentation changes with an already released pack version update `latest` without creating another release. The first successful main build after enabling automation releases the current version if it is still untagged.

Manual version-tag builds remain supported; the tag must match the pack version. Published versions are never overwritten. The workflow uses GitHub's built-in token, so its generated tag and ZIP commit do not trigger another build.

## Distribution and reproducibility

[Packwiz](https://packwiz.infra.link/) metadata pins the Minecraft and Forge versions, exact mod file IDs, checksums, and client/server sides. The server image and client ZIP are built from the same source revision for each release. Use a versioned image tag or digest and the matching client ZIP to reproduce a release.

The client ZIP contains CurseForge file references and shared configuration; CurseForge downloads the specified mods during import. The server downloads its pinned mods at startup and verifies their checksums. Mod JARs, worlds, and player data are not bundled in the repository or image. Embeddium is included on clients only.

Downloads require network access and availability of the upstream files. Published ZIP versions are retained in `client-packs/` with SHA-256 checksums and are never overwritten.
