from aiogram import F,Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State,StatesGroup
from aiogram.types import Message
from sqlalchemy import select

from database.models import Book,SearchLog,User
from database.session import async_session
from handlers.catalog import book_card_text
from handlers.keyboards import main_menu
from aiogram.utils.keyboard import InlineKeyboardBuilder

router=Router()

class SearchState(StatesGroup):
    waiting_query=State()

@router.message(F.text == "🔍 Qidiruv")
async def ask_query(message:Message,state:FSMContext):
    await state.set_state(SearchState.waiting_query)
    await message.answer("Qidirmoqchi bo'lgan kitob nomi yoki muallifini yozing:")

@router.message(SearchState.waiting_query)
async def do_search(message:Message,state:FSMContext):
    query=message.text.strip()
    await state.clear()

    async with async_session() as session:
        user=await session.scalar(select(User).where(User.tg_id==message.from_user.id))

        books=(await session.scalars(
            select(Book).where(
                Book.is_active==True,
                (Book.title.ilike(f"%{query}%")) | (Book.author.ilike(f"%{query}%")),
            )
        )).all()


        session.add(SearchLog(user_id=user.id,query=query,found_count=len(books)))
        await session.commit()

    if not books:
        await state.set_state(SearchState.waiting_query)
        await message.answer(
            " Hech narsa topilmadi.Boshqa nom bilan urinib ko'ring",
            reply_markup=main_menu,
        )
        return

    for book in books:
        kb=InlineKeyboardBuilder()
        if book.stock>0:
            kb.button(text="🛒 Savatga qo'shish", callback_data=f"add_{book.id}")
        kb.adjust(1)

        await message.answer(book_card_text(book),reply_markup=kb.as_markup())

    await state.set_state(SearchState.waiting_query)
    await message.answer("Yana nima izlaysiz?",reply_markup=main_menu)
