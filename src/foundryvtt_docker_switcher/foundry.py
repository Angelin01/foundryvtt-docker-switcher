import json
import httpx
import logging
import re
import aiofiles
import aiofiles.os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WorldInfo:
	id: str
	title: str


@dataclass
class FoundryStatusInactive:
	active: bool
	version: str


@dataclass
class FoundryStatusActive:
	active: bool
	version: str
	world: str
	system: str
	systemVersion: str
	users: int
	uptime: int


FoundryStatus = FoundryStatusInactive | FoundryStatusActive

_WORLD_ENV_PATTERN = re.compile(r'^FOUNDRY_WORLD=.*', re.MULTILINE)


class FoundryAPI:
	def __init__(self, base_url: str):
		self._base_url = base_url
		self._client = httpx.AsyncClient()

	async def get_status(self) -> FoundryStatus:
		response = await self._client.get(f"{self._base_url}/api/status")
		response.raise_for_status()
		data = response.json()
		if data["active"]:
			return FoundryStatusActive(**data)
		return FoundryStatusInactive(**data)

	async def aclose(self):
		await self._client.aclose()

	async def __aenter__(self):
		return self

	async def __aexit__(self, *args):
		await self.aclose()


async def update_world_env(env_path: Path, new_world: str):
	replacement = f'FOUNDRY_WORLD={new_world}'

	try:
		async with aiofiles.open(env_path, 'r+') as f:
			content = await f.read()

			if _WORLD_ENV_PATTERN.search(content):
				new_content = _WORLD_ENV_PATTERN.sub(replacement, content)
			else:
				new_content = content.rstrip() + f"\n{replacement}\n"

			await f.seek(0)
			await f.write(new_content)
			await f.truncate()
	except FileNotFoundError:
		async with aiofiles.open(env_path, 'w') as f:
			await f.write(f"{replacement}\n")
	logger.info(f"Updated {env_path} with world: {new_world}")


async def list_worlds(data_path: Path) -> list[WorldInfo]:
	worlds_dir = data_path / "Data" / "worlds"
	worlds = []

	if not await aiofiles.os.path.isdir(worlds_dir):
		logger.error(f"Worlds directory not found: {worlds_dir}")
		return worlds

	for world_path in (Path(e) for e in await aiofiles.os.listdir(worlds_dir)):
		world_path = worlds_dir / world_path
		if not await aiofiles.os.path.isdir(world_path):
			continue

		world_json_path = world_path / "world.json"
		if not await aiofiles.os.path.exists(world_json_path):
			continue

		try:
			async with aiofiles.open(world_json_path, 'r', encoding='utf-8') as f:
				data = json.loads(await f.read())
				worlds.append(WorldInfo(
					id=data.get("id", world_path.name),
					title=data.get("title", world_path.name),
				))
		except Exception as e:
			logger.error(f"Error reading world.json in {world_path}: {e}")

	return worlds
