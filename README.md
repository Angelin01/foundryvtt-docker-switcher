# foundryvtt-docker-switcher

A Discord bot helper for FoundryVTT instances using [felddy/foundryvtt-docker](https://github.com/felddy/foundryvtt-docker)
that allows switching loaded worlds from Discord.

The bot works by writing an env file with the `FOUNDRY_WORLD` env var and restarting the docker compose project. It
is assumed that this file is mounted in the container. See [Docker Compose Example](#docker-compose-example).

The bot uses with an allowlist of user and role IDs. Users in the allowlist can switch worlds as long as there is no
connected player.

## Image

Built and pushed to GHCR on every push to `main`:

```
ghcr.io/angelin01/foundryvtt-docker-switcher:<version>
```

See the Releases for available versions

## Configuration

All configuration is done via environment variables (or a `.env` file).

| Variable                       | Required | Default                  | Description                                              |
|--------------------------------|----------|--------------------------|----------------------------------------------------------|
| `FDS_DISCORD_TOKEN`            | **Yes**  | —                        | Discord bot token                                        |
| `FDS_FOUNDRY_API_URL`          | No       | `http://localhost:30000` | Base URL of the FoundryVTT instance                      |
| `FDS_FOUNDRY_DATA_PATH`        | No       | `./foundrydata`          | Path to the FoundryVTT data directory                    |
| `FDS_DOCKER_COMPOSE_PROJECT`   | No       | `foundry`                | Docker Compose project name                              |
| `FDS_DOCKER_COMPOSE_DIRECTORY` | No       | `.`                      | Directory containing the `docker-compose.yaml`           |
| `FDS_DOCKER_SERVICE_NAME`      | No       | `foundry`                | Name of the FoundryVTT service in the Compose file       |
| `FDS_ENV_FILE_PATH`            | No       | `foundry.env`            | Path to the env file passed to the FoundryVTT container  |
| `FDS_ALLOWED_USER_IDS`         | No       | ``                       | Comma-separated Discord user IDs allowed to use the bot  |
| `FDS_ALLOWED_ROLE_IDS`         | No       | ``                       | Comma-separated Discord role IDs allowed to use the bot  |
| `FDS_POLL_INTERVAL`            | No       | `60`                     | How often (seconds) to poll FoundryVTT for world changes |

## Docker Compose Example

Below is a full example integrating `foundryvtt-docker-switcher` alongside a FoundryVTT container.

Create a `foundryvtt-docker-switcher.env` file with at least:

```env
FDS_DISCORD_TOKEN=your-discord-bot-token-here
```

And a `foundry.env` file for FoundryVTT secrets (e.g. `FOUNDRY_USERNAME`, `FOUNDRY_PASSWORD`).

```yaml
services:
  foundryvtt:
    image: felddy/foundryvtt:<version>
    container_name: foundryvtt
    hostname: foundryvtt
    restart: unless-stopped
    ports:
      - "30000:30000"
    expose:
      - "30000"
    volumes:
      - ./foundry_data:/data
    environment:
      FOUNDRY_HOSTNAME: localhost
    env_file: "foundry.env"
    secrets:
      - source: config_json
        target: config.json
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL

  foundryvtt-docker-switcher:
    image: ghcr.io/angelin01/foundryvtt-docker-switcher:<version>
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      # Note: if you use secrets, the mount path might have to be the same in the container as it is in the host,
      # otherwise docker compose gets confused when restarting the container.
      - ./:/data
    env_file: "foundryvtt-docker-switcher.env"
    environment:
      FDS_FOUNDRY_API_URL: "http://foundryvtt:30000"
      FDS_FOUNDRY_DATA_PATH: "/data/foundry_data"
      FDS_DOCKER_COMPOSE_PROJECT: "foundryvtt"
      FDS_DOCKER_COMPOSE_DIRECTORY: "/data"
      FDS_DOCKER_SERVICE_NAME: "foundryvtt"
      FDS_ENV_FILE_PATH: "/data/foundry.env"
      FDS_ALLOWED_USER_IDS: "your-discord-user-id"
      FDS_ALLOWED_ROLE_IDS: ""
      FDS_POLL_INTERVAL: "60"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL

secrets:
  config_json:
    file: ./secrets.json
```
