import asyncio
import logging

from aiogram import Bot,Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database.session import init_db
from handlers import start,catalog,search,cart,admin

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()

    bot=Bot(token=BOT_TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp=Dispatcher()
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(search.router)
    dp.include_router(cart.router)
    dp.include_router(admin.router)

    await dp.start_polling(bot)

if __name__=='__main__':
    asyncio.run(main())