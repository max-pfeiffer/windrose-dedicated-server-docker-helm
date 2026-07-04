# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Docker image and Helm chart for running the Windrose dedicated game server (a Windows binary, Steam app 4129620) on Linux via Wine. Three deliverables:

- `build/` — Containerfile plus a Python CLI that builds the image with Podman (via python_on_whales) and publishes it to Docker Hub (`pfeiffermax/windrose-dedicated-server`)
- `charts/windrose/` — Helm chart for Kubernetes deployments
- `examples/docker-compose/` — docker compose example with an update script

## Commands

Python tooling uses uv (Python >= 3.13):

```shell
uv sync

# Run the fast unit tests (tests marked "slow" are deselected by default)
uv run pytest

# Run the slow tests: image build/push to a throwaway local registry plus
# container persistence checks (requires only Podman; slow — the build
# downloads the game server via steamcmd). The build targets linux/amd64;
# on a non-amd64 machine the tests automatically pick the first Podman
# system connection with an amd64 host for build, registry, and test
# containers. Set PODMAN_CONNECTION to pick a connection explicitly.
uv run pytest -m slow

# Run a single test (add -m slow for tests in slow-marked modules, otherwise
# the default addopts deselect them)
uv run pytest tests/test_utils.py::test_create_tag

# Coverage as in CI (fast and slow tests run in separate parallel workflows,
# each uploading its own report to Codecov; the slow workflow adds -m slow)
uv run pytest --cov build --cov-report=xml

# Lint/format (ruff via pre-commit, same as the code-quality CI job)
uv run pre-commit run -a

# Helm chart
helm lint charts/windrose
helm template charts/windrose
```

Ruff is configured in `pyproject.toml` (`src = ["build", "tests"]`, pydocstyle pep257 convention; `charts/` and `examples/` excluded).

## Release automation

Repo releases are automated with release-please (`.github/workflows/release.yaml`, config in `release-please-config.json` / `.release-please-manifest.json`): it runs on push to `main`, collects conventional commits (chart commits under `charts/` are excluded), and maintains a release PR that bumps `pyproject.toml`, updates `CHANGELOG.md`, and tags releases as plain `X.Y.Z` (no `v` prefix). **Commits to `main` must follow conventional commits** (`feat:`, `fix:`, …) to show up in releases.

Docker image and Helm chart releases are separate processes driven independently:

- `.github/workflows/publish.yaml` runs nightly and calls `docker-image.yaml`, which runs `uv run python -m build.publish`. That CLI queries Steam for the current build ID of the Windrose public branch (`build/utils.py:get_windrose_build_id`), and if no `build-<buildid>` tag exists on Docker Hub yet, builds the image with Podman and pushes it tagged `build-<buildid>` and `latest`. `publish-manual.yaml` (workflow_dispatch) forces a build via the `--publish-manually` flag.
- The Helm chart is published by chart-releaser on push to `main` when `charts/**` changes (`helm-release.yaml`). **Bump `version` in `charts/windrose/Chart.yaml` for any chart change**, or the release job will fail on the existing version.

## Docker image architecture

`build/Containerfile` is a two-stage build: the install stage downloads the Windows server files with steamcmd (`+@sSteamCmdForcePlatformType windows`); the production stage is based on `pfeiffermax/debian-wine`, runs as unprivileged user `windrose` (UID/GID 10001), and initializes a Wine prefix under Xvfb at build time.

Runtime flow (`build/scripts/start.sh`, the entrypoint):
1. If `CONFIG_FILE_PATH` / `SECRET_FILE_PATH` are set, source those files as environment variables — this is how the Helm chart injects per-instance config.
2. Run `update_server_description.py`, which writes env vars (`SERVER_NAME`, `PASSWORD`, `INVITE_CODE`, `MAX_PLAYER_COUNT`, etc.) into the server's `ServerDescription.json` and pins `WorldIslandId` to the existing world save if exactly one exists.
3. Start the server executable with `xvfb-run wine`, then tail the server log file (the wine process itself is backgrounded; the tail keeps the container alive).

All persistent state lives in `/srv/windrose/R5/Saved` — that path must be volume-mounted.

## Helm chart architecture

The chart runs **multiple server instances from one StatefulSet**: `replicas` equals `len .Values.instances`. Per-instance wiring is keyed on the pod name (`<fullname>-<index>`):

- The ConfigMap and Secret each contain one entry per instance named after the pod; the StatefulSet mounts them and sets `CONFIG_FILE_PATH`/`SECRET_FILE_PATH` to `/srv/windrose/config/$(POD_NAME)` and `/srv/windrose/secret/$(POD_NAME)`, which `start.sh` sources.
- Each instance gets its own LoadBalancer Service selecting on `statefulset.kubernetes.io/pod-name`, plus a shared headless Service for the StatefulSet.
- `windroseDedicatedServer.existingSecret` suppresses Secret creation and uses the named secret instead.
- The chart hardcodes `USE_DIRECT_CONNECTION=true` in the ConfigMap: the ICE/P2P mode uses dynamic ports, which is incompatible with Kubernetes networking.
- Startup/liveness probes are `nc` UDP checks against the server port; server startup (world generation) is slow, hence the high startup `failureThreshold`.

## Tests

Tests live in `tests/` and exercise the build tooling, not the game server. Slow tests are marked `slow` and deselected by default (`addopts = "-m 'not slow'"` in `pyproject.toml`); the image is built **once per session** by the session-scoped `published_image` fixture in `conftest.py` and shared by all slow tests:

- `test_image_build.py` (slow) asserts the image was pushed to a throwaway local registry with the `build-<buildid>` and `latest` tags. Everything runs with Podman (the registry is a `registry:2` container started by the session-scoped `registry` fixture, no Docker needed) and takes significant time/disk. Podman on the build host must trust the registry address as an insecure registry (see `test-image-build.yaml` for CI; on macOS that means inside the Podman machine or on the remote build host, plus the local client config in `~/.config/containers/registries.conf.d/` for `podman login`). The `podman_connection` fixture selects the Podman system connection used for build, registry, and test containers: `PODMAN_CONNECTION` if set, otherwise the default host when it is amd64, otherwise the first connection with an amd64 host (steamcmd in the install stage is a 32-bit x86 binary that cannot be emulated on arm64). With a remote connection the registry is addressed via the connection's host instead of `localhost:5000`.
- `test_container.py` (slow) runs a container from the built image and verifies `PersistentServerId` and `WorldIslandId` survive container restarts. It only waits for the entrypoint's config phase (the "ServerDescription.json modified" log line) and never waits for the Wine/world-generation server startup.
- `test_publish.py` unit-tests the publish CLI with mocks. `test_update_server_description.py` tests the container's config-injection script against `tests/assets/ServerDescription.json`. Note that `build/scripts/update_server_description.py` is a standalone script copied into the image; it must stay stdlib-only (the container only has `python3`, no pip packages).
