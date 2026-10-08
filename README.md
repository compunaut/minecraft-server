# Glass House: private Epic Fight server and client pack

This repository is the source of truth for Minecraft **1.20.1**, **Forge 47.4.10**, the eleven tested Epic Fight gameplay mods, and **Embeddium 0.3.31** on clients only. Packwiz pins every CurseForge project, file ID, filename, side, and checksum. The server image and client ZIP derive from the same commit and release tag. The source repository and client ZIP releases remain private. The GHCR image is intended for public pulls after the owner sets its package visibility to Public.

## First deployment

Use Docker Engine with the Compose plugin on Linux, or Docker Desktop on a Mac. A running Docker daemon is required. For Raspberry Pi 5, use **64-bit** Raspberry Pi OS and ARM64 Docker; a Pi 3 is not a supported performance target. The published image supports `linux/amd64` and `linux/arm64` automatically.

First merge the setup PR, wait for the main build to succeed, then create tag `v1.0.0` at that validated commit and push it. The tag must equal `v` plus `pack.toml`'s version. The tag workflow publishes the image before attaching the client ZIP to a private GitHub Release. Wait for the entire workflow to finish before distributing a new release.

Clone this repository on the server host. Copy `.env.example` to `.env`. Read [Minecraft's EULA](https://aka.ms/MinecraftEULA), then explicitly set `EULA=TRUE`. Set `IMAGE_TAG=v1.0.0` and choose your memory limit.

The default maximum heap is **16G** for the owner's 64 GB Mac. Set `MEMORY=4G` for an 8 GB Raspberry Pi 5, leaving space for the OS and Java overhead; tune view/simulation distances after testing. `JVM_OPTS` adds flags, but do not put competing `-Xmx` or `-Xms` flags in it. This is a Java heap limit, not a container-wide RAM limit.

Once the owner makes the GHCR package Public, no login is required:

```sh
docker compose pull
docker compose up -d
docker compose logs -f
```

Until that setting is applied, pulls require a GitHub account with package access and a classic PAT with `read:packages`, supplied to `docker login ghcr.io` using `--password-stdin`. Never put tokens in shell history or this repo. Public GHCR visibility does not expose the private source repo, private client ZIP releases, or any world data.

GitHub Actions uses its built-in `GITHUB_TOKEN` with `packages:write`; no saved PAT or mod download secret is needed for builds. Verify Actions is enabled, allowed to write packages and release contents, and permitted to use the referenced actions. In package settings, the owner should set visibility **Public**, keep the repository linked, and grant its Actions workflow access if an existing package does not inherit it. Give players repository access to download the private release, or share the ZIP through an agreed private channel. Players do not need container registry access.

## Existing world and local server

Your live folder is **not** the Git checkout or image build context. Stop the old server with `stop` and wait until it exits before making a backup or copying data. Never let the old server and container access the same world simultaneously.

After backing up the entire old server, create `minecraft-data/` beside Compose. Copy the world's actual `level-name` directory (normally `world/`) into it, along with `server.properties`, `ops.json`, `whitelist.json`, and ban lists if desired. Standard Forge Nether/End dimensions are inside the world; preserve the entire directory including `serverconfig`. Keep all migration data out of Git. Do not copy old `mods/`, `libraries/`, Packwiz runtime state, or installers. On first start, the container installs the canonical mods and config defaults.

The old server's `user_jvm_args.txt` was separately changed to `-Xms4G -Xmx16G` at the owner's request. Restart that server to apply it; the repository does not control that local script. When migrating to Docker, use `.env`'s `MEMORY` instead.

## Running, stopping and backups

```sh
docker compose logs -f
docker compose restart
docker compose down
```

`down` allows two minutes for the upstream server runner to save and stop on SIGTERM. Data persists in `./minecraft-data`. Do not force-kill the container or use a short shutdown timeout. Server properties, worlds, player lists, and world-specific server configs persist there. Compose sets `OVERRIDE_SERVER_PROPERTIES=false`, so existing properties are retained. RCON is disabled by default; no baked-in password is exposed.

Make a cold backup after stopping:

```sh
docker compose down
mkdir -p backups
tar -czf "backups/server-$(date +%Y%m%d-%H%M%S).tar.gz" minecraft-data
docker compose up -d
```

Keep copies on another device and test restoration. The entire data directory captures the world, settings, and pack installation state. Config files listed in the pack are managed defaults: upgrades proceed only when current copies match either the previous managed version or the new version. Local edits cause an explicit failure rather than silently overwriting them. Incorporate intentional shared config changes into the pack. World `serverconfig` values are persistent and need separate compatibility review; default configs alone do not override them.

## Updates and rollback

Before updating, back up while stopped. Change `.env` to the new immutable `IMAGE_TAG`, then:

```sh
docker compose pull
docker compose up -d
docker compose logs -f
```

Have every player install the client ZIP with the same version. An upgrade removes previously managed mods that are absent from the new pack. Unknown JARs cause a failure; extra local mods are not accepted silently. All downloaded files are checksum-verified before Minecraft starts. Downloads require Internet access on first start; valid files are cached under `/data/.pack-cache` for restarts. Forge/Mojang downloads may still be needed. The image contains pack definitions, not an offline ready-to-run server.

To roll back safely, stop, restore the **pre-upgrade data backup**, change `IMAGE_TAG` to the previous release, pull and start. Merely downgrading an image does not undo world format or mod data changes. Restore into an empty data directory so new files do not survive the rollback. Never reuse or move a published version tag. Prefer the published image digest for strongest deployment pinning; `latest` is convenient for development but should not be used for family deployments.

## Clients

Download `epic-fight-pack-vX.Y.Z.zip` from this repository's [Releases](https://github.com/compunaut/minecraft-server/releases). In CurseForge, choose Minecraft, **Import** / **Import Profile**, and select the ZIP. Launch that exact profile, then connect to the server address. Do not manually update individual mods, substitute similarly named addons, or reuse an old profile for a new release. Embeddium is client-only and never installed on the dedicated server.

Report the pack release version, exact mod mismatch message, and relevant log excerpt if joining fails. Remove addresses, usernames or other private details before posting. Both sides use the same Forge and gameplay file IDs.

## Changing mods with Packwiz

Use Go 1.25+ and Python 3.11+ (or Python 3.8+ with `tomli`). Install the pinned Packwiz revision:

```sh
scripts/install-packwiz.sh
export PATH="$PWD/.cache/bin:$PATH"
```

Create a branch. To change a mod, use its **exact CurseForge file URL** with `packwiz curseforge add https://www.curseforge.com/minecraft/mc-mods/PROJECT/files/FILE_ID`; inspect the resulting metadata and verify the intended project identity. Keep gameplay mods `side="both"`, Embeddium `side="client"`. Do not run bulk update blindly. Minecraft stays 1.20.1. Forge updates require explicit compatibility review and must change `pack.toml`, which controls both image runtime and client manifest.

Bump `pack.toml`'s semantic pack version (independent of the Minecraft version), run:

```sh
packwiz refresh
scripts/validate-pack.sh --fetch
scripts/build-client-pack.sh
```

Commit the metadata and config changes, open a PR, and wait for CI. Test the image on a disposable copy of a world, then test a matching client joining and the combat addons. Merge only after these checks. Create `vX.Y.Z` at that exact main commit. CI validates all downloads, builds both architectures, publishes `latest` only on main plus long `sha-...` and version tags, and attaches the exact client ZIP plus SHA-256 to the Release after image publication.

`index.toml` and `pack.toml` hashes are refreshed only after intended changes. `.packwizignore` keeps build scripts, documentation and runtime files out of the client pack. If adding a project, explicitly review the identity allowlist in `scripts/pack.py`; version updates otherwise stay entirely in Packwiz. CI checks mandatory Forge dependencies on each side, including bundled Forge mod metadata. It fails closed on unsupported version range syntax. These checks do not prove addon behavior or optional interactions.

## Distribution and reproducibility

[Packwiz's CurseForge export](https://packwiz.infra.link/tutorials/hosting/curseforge/) emits pinned file references for CurseForge mods. Our exporter verifies all twelve references, versions and sides, and rejects any JAR bundled in the ZIP or unexpected overrides. Friends import one ZIP; CurseForge downloads the files. If a mod becomes unavailable, the workflow fails; do not silently omit or replace it.

Server downloads use the public CurseForge CDN path for each pinned file and verify its Packwiz checksum. No binary mods are committed or redistributed in GHCR. This does not assert a blanket license to redistribute individual mods. If a project's author disables distribution or a file disappears, installation/validation fails; obtain permission or deliberately review a supported alternative. Do not bypass access restrictions or manually bundle such files. Project/file IDs and exact hashes are pinned; the upstream Java 17 multi-architecture base (2026.9.2-java17) is pinned by manifest digest and the TOML parser wheel is pinned by version and SHA-256. OS package installation and Forge/Mojang downloads are network-dependent, so this is a repeatable, integrity-checked pack build rather than a byte-for-byte offline build.

## Import findings and validation limits

The imported local folder had eleven matching gameplay mods and no Embeddium metadata. Embeddium 0.3.31 was added as a pinned client-only dependency. Its client behavior still needs a real client test. The local `pack.toml` said Forge 47.4.23, but installed launch arguments and logs identify **47.4.10**; the pack now matches the actually installed server. No Forge upgrade was performed.

The old index contained player/runtime files and libraries. It was rebuilt from selected mod metadata and reviewed gameplay configs only. No worlds, player lists, server addresses, logs, binaries or resource packs were imported. EWU and Resurrection Vanillafied 3D are excluded. Weapons of Miracles is retained as the Fantasy Weapons EpicFied dependency.

The image uses the maintained [itzg server](https://github.com/itzg/docker-minecraft-server) for Forge installation, JVM settings and graceful shutdown. A small wrapper reads the baked-in Packwiz metadata and verifies/downloads the exact server files before delegating to its runner. This avoids serving private metadata over HTTP and keeps credentials out of the image. The canonical loader cannot be overridden through environment variables. Full amd64/arm64 startup, clean shutdown and a client joining must be tested before the first production release; a successful image build alone is insufficient.

## Workflow runtimes and attestations

Both workflows use Ubuntu 24.04 explicitly. All JavaScript actions are pinned to verified Node 24 revisions, with readable major-version comments. Go dependency caching is disabled because this is a Packwiz-managed pack, not a Go module with a `go.sum` file.

Published GHCR images include BuildKit `mode=max` provenance and an SPDX SBOM attestation for each architecture. Provenance records the build definition and source revision; no secrets are passed through build arguments. The SBOM covers software in the container image. Gameplay mod JARs downloaded at runtime are not in the image SBOM; their identities and hashes remain in the canonical Packwiz metadata. These BuildKit attestations describe the build and are not a claim that the image has been separately signed by GitHub's artifact-attestation service.

For signed GitHub release attestations on client ZIPs, the owner enables **Settings → Releases → Enable release immutability** on GitHub. This applies to future releases and automatically creates a release attestation covering the tag, commit, and assets. The release workflow creates a draft with its ZIP and checksum attached, then publishes it so the complete asset set is locked together. Existing releases and previously shared ZIP files are not changed. The owner manages these website settings; the workflow cannot silently enable repository immutability or package visibility.

See [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases) and [Docker attestations](https://docs.docker.com/build/ci/github-actions/attestations/).
