# Dev Container configuration for switchbot-ble-to-influxdb

This configuration enables development in GitHub Codespaces or locally with VS Code Remote - Containers.

- Python 3.12 (via official dev container image)
- Installs all dependencies with `uv sync --dev`
- Includes recommended VS Code extensions for Python, Docker, and GitHub
- Forwards port 8086 (InfluxDB default)

## Usage

1. Open this repository in GitHub Codespaces, or locally in VS Code and select "Reopen in Container".
2. The environment will be ready for development and testing.

See `.devcontainer/devcontainer.json` for details.
