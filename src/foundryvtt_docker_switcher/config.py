import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

@dataclass(frozen=True)
class Config:
	discord_token: str
	foundry_api_url: str
	foundry_data_path: Path
	docker_compose_project: str
	docker_compose_directory: Path
	docker_service_name: str
	env_file_path: Path
	allowed_user_ids: list[int]
	allowed_role_ids: list[int]
	poll_interval: int

def _parse_int_list(value: str | None) -> list[int]:
	if not value:
		return []
	return [int(v.strip()) for v in value.split(",") if v.strip()]

def load_config() -> Config:
	load_dotenv()

	discord_token = os.getenv("FDS_DISCORD_TOKEN")
	if not discord_token:
		raise ValueError("FDS_DISCORD_TOKEN environment variable is required")

	return Config(
		discord_token=discord_token,
		foundry_api_url=os.getenv("FDS_FOUNDRY_API_URL", "http://localhost:30000").rstrip("/"),
		foundry_data_path=Path(os.getenv("FDS_FOUNDRY_DATA_PATH", "./foundrydata")),
		docker_compose_project=os.getenv("FDS_DOCKER_COMPOSE_PROJECT", "foundry"),
		docker_compose_directory=Path(os.getenv("FDS_DOCKER_COMPOSE_DIRECTORY", ".")),
		docker_service_name=os.getenv("FDS_DOCKER_SERVICE_NAME", "foundry"),
		env_file_path=Path(os.getenv("FDS_ENV_FILE_PATH", "foundry.env")),
		allowed_user_ids=_parse_int_list(os.getenv("FDS_ALLOWED_USER_IDS")),
		allowed_role_ids=_parse_int_list(os.getenv("FDS_ALLOWED_ROLE_IDS")),
		poll_interval=int(os.getenv("FDS_POLL_INTERVAL", "60")),
	)
