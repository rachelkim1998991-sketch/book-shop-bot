from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from sqlalchemy import select, func

from config import ADMIN_IDS
from database.models import OrderItem, Order, Book, SearchLog
from database.session import async_session
from handlers.keyboards import admin_menu, main_menu

router=Router()

def is_admin(user_id:int)->bool:
    return user_id in ADMIN_IDS

class AddBookState(StatesGroup):
    title=State()
    author=State ()
    description=State()
    price=State()
    stock=State()

class UpdateStockState(StatesGroup):
    book_id=State()
    new_stock=State()

@router.message(Command("admin"))
async def admin_start(message:Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda admin huquqi yo'q")
        return
    await message.answer("🔧 Admin panelga xush kelibsiz.",reply_markup=admin_menu)


@router.message(F.text=="⬅️ Chiqish")
async def admin_exit(message:Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Asosiy menyu.",reply_markup=main_menu)

@router.message(F.text=="📊 Statistika")
async def show_stats(message:Message):
    if not is_admin(message.from_user.id):
        return

    async with async_session() as session:
        sold_subq=(
            select(
                OrderItem.book_id,
                func.sum(OrderItem.quantity).label("sold"),
            )
            .join(Order,Order.id==OrderItem.order_id)
            .where(Order.status!="cart")
            .group_by(OrderItem.book_id)
            .subquery()
        )

        rows=(await session.execute(
            select(Book.title,Book.stock,func.coalesce(sold_subq.c.sold,0))
            .outerjoin(sold_subq,sold_subq.c.book_id==Book.id)
            .order_by(Book.title)
        )).all()

        top_searches=(await session.execute(
            select(SearchLog.query,func.count(SearchLog.id).label("cnt"))
            .group_by(SearchLog.query)
            .order_by(func.count(SearchLog.id).desc())
            .limit(10)
        )).all()

        not_found=(await session.execute(
            select(SearchLog.query,func.count(SearchLog.id).label("cnt"))
            .where(SearchLog.found_count==0)
            .group_by(SearchLog.query)
            .order_by(func.count(SearchLog.id).desc())
            .limit(10)
        )).all()

    lines=["<b>📊 Kitoblar statistikasi</b>\n"]
    for title,stock,sold in rows:
        lines.append(f"• {title} — sotilgan: <b>{sold}</b>, qolgan: <b>{stock}</b>")

    lines.append("\n<b>🔍 Eng ko'p qidirilgan so'zlar</b>")
    if top_searches:
        for query,cnt in top_searches:
            lines.append(f"• {query} — {cnt} marta")

    else:
        lines.append("Hozircha ma'lumot yo'q")

    lines.append("\n<b>❗ Qidirilgan, lekin topilmagan so'zlar</b>")
    if not_found:
        for query,cnt in not_found:
            lines.append(f"• {query} — {cnt} marta")
    else:
        lines.append("Yo'q-hammasi topilgan")

    await message.answer("\n".join(lines))



@router.message(F.text == "📚 Kitoblar ro'yxati")
async def admin_book_list(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with async_session() as session:
        books = (await session.scalars(select(Book).order_by(Book.id))).all()

    if not books:
        await message.answer("Kitoblar yo'q.")
        return

    lines = ["<b>📚 Kitoblar ro'yxati</b>\n"]
    for book in books:
        status = "✅ faol" if book.is_active else "❌ nofaol"
        lines.append(
            f"#{book.id} <b>{book.title}</b> — {book.author}\n"
            f"   💰 {int(book.price):,} so'm | 📦 qoldiq: {book.stock} | {status}"
        )

    await message.answer("\n".join(lines))

@router.message(F.text == "➕ Kitob qo'shish")
async def add_book_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddBookState.title)
    await message.answer("Kitob nomini kiriting:")


@router.message(AddBookState.title)
async def add_book_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddBookState.author)
    await message.answer("Muallifini kiriting:")


@router.message(AddBookState.author)
async def add_book_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text.strip())
    await state.set_state(AddBookState.description)
    await message.answer("Qisqacha tavsif kiriting (yoki '-' deb yozing):")


@router.message(AddBookState.description)
async def add_book_description(message: Message, state: FSMContext):
    desc = message.text.strip()
    await state.update_data(description=None if desc == "-" else desc)
    await state.set_state(AddBookState.price)
    await message.answer("Narxini kiriting (faqat raqam, masalan 55000):")


@router.message(AddBookState.price)
async def add_book_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting. Masalan: 55000")
        return
    await state.update_data(price=price)
    await state.set_state(AddBookState.stock)
    await message.answer("Miqdorini kiriting (nechta dona, masalan 10):")


@router.message(AddBookState.stock)
async def add_book_stock(message: Message, state: FSMContext):
    try:
        stock = int(message.text.strip())
    except ValueError:
        await message.answer("Iltimos, faqat butun son kiriting. Masalan: 10")
        return

    data = await state.get_data()
    await state.clear()

    async with async_session() as session:
        session.add(Book(
            title=data["title"],
            author=data["author"],
            description=data["description"],
            price=data["price"],
            stock=stock,
        ))
        await session.commit()

    await message.answer(
        f"✅ Kitob qo'shildi: <b>{data['title']}</b>",
        reply_markup=admin_menu,
    )

@router.message(F.text == "✏️ Qoldiqni yangilash")
async def update_stock_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(UpdateStockState.book_id)
    await message.answer("Kitob ID raqamini kiriting (ro'yxatni '📚 Kitoblar ro'yxati'dan ko'rasiz):")


@router.message(UpdateStockState.book_id)
async def update_stock_book_id(message: Message, state: FSMContext):
    try:
        book_id = int(message.text.strip())
    except ValueError:
        await message.answer("Iltimos, faqat butun son (ID) kiriting.")
        return

    async with async_session() as session:
        book = await session.get(Book, book_id)

    if book is None:
        await message.answer("Bunday ID'li kitob topilmadi. Qaytadan urinib ko'ring:")
        return

    await state.update_data(book_id=book_id, book_title=book.title)
    await state.set_state(UpdateStockState.new_stock)
    await message.answer(f"<b>{book.title}</b> — yangi qoldiq sonini kiriting:")


@router.message(UpdateStockState.new_stock)
async def update_stock_new_value(message: Message, state: FSMContext):
    try:
        new_stock = int(message.text.strip())
    except ValueError:
        await message.answer("Iltimos, faqat butun son kiriting.")
        return

    data = await state.get_data()
    await state.clear()

    async with async_session() as session:
        book = await session.get(Book, data["book_id"])
        book.stock = new_stock
        await session.commit()

    await message.answer(
        f"✅ '{data['book_title']}' uchun yangi qoldiq: {new_stock} dona",
        reply_markup=admin_menu,
    )

