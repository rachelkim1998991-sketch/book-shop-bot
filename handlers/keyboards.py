from aiogram.types import KeyboardButton,ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

main_menu=ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Katalog"),KeyboardButton(text="🔍 Qidiruv")],
        [KeyboardButton(text="🛒 Savat"),KeyboardButton(text="📦 Buyurtmalarim")],
    ],
    resize_keyboard=True,
)

admin_menu=ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📚 Kitoblar ro'yxati")],
        [KeyboardButton(text="➕ Kitob qo'shish"), KeyboardButton(text="✏️ Qoldiqni yangilash")],
        [KeyboardButton(text="⬅️ Chiqish")],
    ],
    resize_keyboard=True,
)