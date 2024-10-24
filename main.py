import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.handlers import router


logging.basicConfig(level=logging.INFO)

bot_token = os.getenv('BOT_TOKEN')

bot = Bot(token=bot_token)
dp = Dispatcher(storage=MemoryStorage())


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
