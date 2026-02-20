import asyncio
import logging
import discord
from discord import app_commands
from .config import Config
from .foundry import FoundryAPI, FoundryStatusActive, list_worlds, update_world_env
from .docker import restart_service

logger = logging.getLogger(__name__)


def _is_allowed(interaction: discord.Interaction, config: Config) -> bool:
	if interaction.user.id in config.allowed_user_ids:
		return True
	if isinstance(interaction.user, discord.Member):
		if any(role.id in config.allowed_role_ids for role in interaction.user.roles):
			return True
	return False


class SwitcherBot(discord.Client):
	def __init__(self, config: Config):
		intents = discord.Intents.default()
		super().__init__(intents=intents)
		self.config = config
		self.foundry = FoundryAPI(config.foundry_api_url)
		self.tree = app_commands.CommandTree(self)

	def register_commands(self):
		@self.tree.command(name="switch-world", description="Switch the active FoundryVTT world")
		@app_commands.describe(world="The world to switch to")
		async def switch_world(interaction: discord.Interaction, world: str):
			if not _is_allowed(interaction, self.config):
				await interaction.response.send_message("You are not allowed to run this command.", ephemeral=True)
				return

			worlds = await list_worlds(self.config.foundry_data_path)
			match = next((w for w in worlds if w.id == world), None)
			if match is None:
				await interaction.response.send_message(f"World '{world}' not found.", ephemeral=True)
				return

			status = await self.foundry.get_status()
			if isinstance(status, FoundryStatusActive) and status.users > 0:
				await interaction.response.send_message(f"Cannot switch worlds: there are {status.users} active user(s) in the current world.")
				return

			logger.info(f"User {interaction.user} requested switch to world '{match.id}'")
			await interaction.response.send_message(f"Switching to world **{match.title}**...")
			await update_world_env(self.config.env_file_path, match.id)
			await restart_service(self.config.docker_compose_project, self.config.docker_service_name)

		@switch_world.autocomplete("world")
		async def switch_world_autocomplete(
			interaction: discord.Interaction, current: str
		) -> list[app_commands.Choice[str]]:
			worlds = await list_worlds(self.config.foundry_data_path)
			return [
				app_commands.Choice(name=w.title, value=w.id)
				for w in worlds
				if current.lower() in w.title.lower()
			][:25]

	async def setup_hook(self):
		await self.tree.sync()
		logger.info("Slash commands synced")
		self.loop.create_task(self._poll_foundry())

	async def on_ready(self):
		logger.info(f"Logged in as {self.user}")

	async def _poll_foundry(self):
		await self.wait_until_ready()
		while not self.is_closed():
			try:
				status = await self.foundry.get_status()
				if isinstance(status, FoundryStatusActive):
					activity = discord.Game(name=f"{status.world} ({status.users} online)")
					presence_status = discord.Status.online
				else:
					activity = discord.Game(name="No active world")
					presence_status = discord.Status.idle
			except Exception as e:
				logger.exception("Failed to poll Foundry status", exc_info=e)
				activity = discord.Game(name="Foundry unreachable")
				presence_status = discord.Status.do_not_disturb

			await self.change_presence(status=presence_status, activity=activity)
			await asyncio.sleep(self.config.poll_interval)
