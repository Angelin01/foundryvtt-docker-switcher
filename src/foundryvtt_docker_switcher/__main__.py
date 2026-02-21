import asyncio
import logging
from .config import load_config
from .bot import SwitcherBot

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


async def main():
	config = load_config()
	bot = SwitcherBot(config)
	bot.register_commands()
	try:
		await bot.start(config.discord_token)
	except asyncio.CancelledError | KeyboardInterrupt:
		pass
	finally:
		if not bot.is_closed():
			await bot.close()
		await bot.foundry.aclose()


def run():
	asyncio.run(main())


if __name__ == "__main__":
	run()
