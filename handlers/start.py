from html import escape

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select

from database.models import User
from database.session import async_session
from handlers.keyboards import main_menu

router=Router()

@router.message(CommandStart())
async def cmd_start(message:Message):
    tg=message.from_user

    async with async_session() as session:
        user=await session.scalar(select(User).where(User.tg_id==tg.id))
        if user is None:
            session.add(User(tg_id=tg.id,full_name=tg.full_name,username=tg.username))
            await session.commit()

    await message.answer(
        f"Assalomu alaykum,<b>{escape(tg.full_name)}</b>!📚\n"
        "Kitob do'koni botiga xush kelibsiz.",
        reply_markup=main_menu,
    )
