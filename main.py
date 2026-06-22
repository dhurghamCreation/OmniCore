import asyncio
from game import main


async def run_game():
	await main()


if __name__ == "__main__":
	asyncio.run(run_game())
