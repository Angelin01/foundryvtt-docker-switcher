import asyncio
import logging
from .config import load_config
from .bot import SwitcherBot

logging.basicConfig(level=logging.INFO)


async def main():
	config = load_config()
	bot = SwitcherBot(config)
	bot.register_commands()
	await bot.start(config.discord_token)


def run():
	asyncio.run(main())


if __name__ == "__main__":
	run()
