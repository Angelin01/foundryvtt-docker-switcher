import asyncio
import logging
from pathlib import Path

from python_on_whales import DockerClient

logger = logging.getLogger(__name__)


async def restart_service(project: str, directory: Path, service: str):
	logger.info(f"Restarting service '{service}' in project '{project}'")
	client = DockerClient(compose_project_name=project, compose_project_directory=directory)
	loop = asyncio.get_event_loop()
	await loop.run_in_executor(None, lambda: client.compose.up([service], detach=True, force_recreate=True))
	logger.info(f"Service '{service}' restarted successfully")
