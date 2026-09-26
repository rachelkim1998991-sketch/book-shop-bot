from aiogram import F,Router
from aiogram.types import CallbackQuery,Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import Order, User, Book, OrderItem
from database.session import async_session
from handlers.keyboards import main_menu

router=Router()

async def get_or_create_cart(session,user_id:int)->Order:
    cart=await session.scalar(
        select(Order).where(Order.user_id==user_id,Order.status=="cart")
    )
    if cart is None:
        cart=Order(user_id=user_id,status="cart",total=0)
        session.add(cart)
        await session.flush()
    return cart

@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback:CallbackQuery):
    book_id=int(callback.data.split("_")[1])

    async with async_session() as session:
        user=await session.scalar(select(User).where(User.tg_id==callback.from_user.id))
        book=await session.get(Book,book_id)

        if book is None or book.stock<=0:
            await callback.answer("Kechirasiz,bu kitob hozir mavjud emas.",show_alert=True)
            return

        cart=await get_or_create_cart(session,user.id)

        item=await session.scalar(
            select(OrderItem).where(OrderItem.order_id==cart.id,OrderItem.book_id==book.id)
        )
        if item:
            if item.quantity+1>book.stock:
                await callback.answer("Omborda shuncha kitob yo'q.",show_alert=True)
                return
            item.quantity+=1
        else:
            session.add(OrderItem(order_id=cart.id,book_id=book.id,quantity=1,price=book.price))

        await session.commit()

    await callback.answer("🛒 Savatga qo'shildi!")

@router.message(F.text=="🛒 Savat")
async def show_cart(message:Message):
    async with async_session() as session:
        user=await session.scalar(select(User).where(User.tg_id==message.from_user.id))

        cart=await session.scalar(
            select(Order)
            .where(Order.user_id==user.id,Order.status=="cart")
            .options(selectinload(Order.items).selectinload(OrderItem.book))
        )

        if cart is None or not cart.items:
            await message.answer("🛒 Savatingiz bo'sh.", reply_markup=main_menu)
            return

        lines= ["<b>🛒 Sizning savatingiz:</b>\n"]
        total=0
        for item in cart.items:
            subtotal=float(item.price)*item.quantity
            total+=subtotal
            lines.append(
                 f"• {item.book.title} — {item.quantity} dona × {int(item.price):,} so'm = {int(subtotal):,} so'm"
            )
        lines.append(f"\n💰 <b>Jami: {int(total):,} so'm</b>")

        kb=InlineKeyboardBuilder()
        kb.button(text="✅ Buyurtma berish", callback_data="checkout")
        kb.button(text="🗑 Tozalash", callback_data="clear_cart")
        kb.adjust(1)

        await message.answer("\n".join(lines), reply_markup=kb.as_markup())

@router.callback_query(F.data=="clear_cart")
async def clear_cart(callback:CallbackQuery):
    async with async_session() as session:
        user=await session.scalar(select(User).where(User.tg_id==callback.from_user.id))
        cart=await session.scalar(
            select(Order).where(Order.user_id==user.id,Order.status=="cart")
        )
        if cart:
            for item in await session.scalars(select(OrderItem).where(OrderItem.order_id==cart.id)):
                await session.delete(item)
            await session.delete(cart)
            await session.commit()
    await callback.message.edit_text("🗑 Savat tozalandi.")
    await callback.answer()

@router.callback_query(F.data=="checkout")
async def checkout(callback:CallbackQuery):
    async with async_session() as session:
        user=await session.scalar(select(User).where(User.tg_id==callback.from_user.id))

        cart=await session.scalar(
            select(Order)
            .where(Order.user_id==user.id,Order.status=="cart")
            .options(selectinload(Order.items).selectinload(OrderItem.book))
        )

        if cart is None or not cart.items:
            await callback.answer("Savat bo'sh",show_alert=True)
            return

        for item in cart.items:
            if item.quantity>item.book.stock:
                await callback.answer(
                    f"'{item.book.title}' kitobidan omborda yetarli emas.",show_alert=True
                )
                return

        total=0
        for item in cart.items:
            item.book.stock-=item.quantity
            total+=float(item.price)*item.quantity

        cart.status="new"
        cart.total=total

        await session.commit()

    await callback.message.edit_text(
        f"✅ Buyurtmangiz qabul qilindi!\n💰 Jami: {int(total):,} so'm\n\n"
        "Tez orada siz bilan bog'lanamiz."
    )
    await callback.answer()

@router.message(F.text== "📦 Buyurtmalarim")
async def my_orders(message:Message):
    async with async_session() as session:
        user=await session.scalar(select(User).where(User.tg_id==message.from_user.id))

        orders=(await session.scalars(
            select(Order)
            .where(Order.user_id==user.id,Order.status!="cart")
            .options(selectinload(Order.items).selectinload(OrderItem.book))
            .order_by(Order.created_at.desc())
        )).all()

        if not orders:
            await message.answer("Sizda hali buyurtmalar yo'q",reply_markup=main_menu)
            return

        lines=["<b>📦 Sizning buyurtmalaringiz:</b>\n"]
        for order in orders:
            date_str=order.created_at.strftime("%d.%m.%Y %H:%M")
            lines.append(f"\n🧾 <b>#{order.id}</b> — {date_str}")
            for item in order.items:
                lines.append(f"  • {item.book.title} × {item.quantity}")
            lines.append(f"  💰 Jami: {int(order.total):,} so'm")
        await message.answer("\n".join(lines), reply_markup=main_menu)