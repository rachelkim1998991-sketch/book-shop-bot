from aiogram import F,Router
from aiogram.types import CallbackQuery,Message
from sqlalchemy import select

from database.models import Book
from database.session import async_session
from aiogram.utils.keyboard import InlineKeyboardBuilder

router=Router()

def book_card_text(book:Book)->str:
    stock_line=f"✅ Mavjud" if book.stock> 0 else " ❌ Hozircha yo'q"
    return(
        f"<b>{book.title}</b>\n"
        f"✍️ {book.author}\n\n"
        f"{book.description or ''}\n\n"
        f"💰 <b>{int(book.price):,} so'm</b>\n"
        f"{stock_line}"
    )

@router.message(F.text=="📚 Katalog")
async def show_catalog(message:Message):
    async with async_session() as session:
        books=(await session.scalars(
            select(Book).where(Book.is_active==True).order_by(Book.id)
        )).all()

    if not books:
        await message.answer("Hozircha kitoblar mavjud emas")
        return

    for book in books:
        kb=InlineKeyboardBuilder()
        if book.stock>0:
            kb.button(text="🛒 Savatga qo'shish",callback_data=f"add_{book.id}")
        kb.adjust(1)

        await message.answer(book_card_text(book),reply_markup=kb.as_markup())