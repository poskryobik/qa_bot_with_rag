from handlers import different_types, chat
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import asyncio
import logging
import sys
import os




sys.path.append(os.getcwd())
load_dotenv()

bot_token = os.getenv("TOKEN")
logging.basicConfig(level=logging.INFO)


# Запуск бота
async def main():
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    dp.include_routers(chat.router, different_types.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())