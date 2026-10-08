# Import validation (2026-10-08)

Passed locally:
- All twelve pinned CurseForge files downloaded from the public CDN and matched Packwiz hashes.
- The eleven local gameplay JARs matched the corresponding imported Packwiz hashes.
- Mandatory Forge dependencies and version ranges resolved on both client and server sides.
- EpicFight Extra bundles Invincible 20.14.7.5; the explicit 20.14.8.2 satisfies its declared bundled range. Top-level duplicate IDs remain errors.
- Exported client ZIP contains exactly twelve required CurseForge references, Minecraft 1.20.1, Forge 47.4.10, pack version 1.0.0, and selected config overrides. No JARs or runtime data are bundled.
- Isolated server installation and repeat startup install exactly eleven gameplay JARs and exclude Embeddium.
- Unknown server JARs, locally edited managed configs, and stale index hashes are rejected.
- Compose validation with Docker Desktop's bundled Compose binary, workflow YAML parsing, config parsing, and shell syntax checks passed.
- Local native JVM settings are now -Xms4G and -Xmx16G; no server restart was performed.

Not tested locally:
- Docker image build and startup: the Docker engine was unavailable. GitHub Actions performs the amd64/arm64 builds.
- Dedicated server clean shutdown, actual player join, addon behavior, client rendering, and Raspberry Pi performance. These require runtime acceptance testing before a production release.
- GHCR publication and GitHub Release creation: these occur after merge/tag and require successful Actions runs.

No world or player files were imported. Source server files were left unchanged except the explicitly requested JVM memory setting. No license grants were inferred; client distribution uses CurseForge references and server mods are downloaded at runtime rather than redistributed in the image.
